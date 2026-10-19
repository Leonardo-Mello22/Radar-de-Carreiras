"""Generate the analysis plan and its traceability matrices from one content source."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "01_plano_de_analise"
DATA = ROOT / "datasets"

QUESTIONS = [
    {"id": "P1", "base": "CAGED", "pergunta": "Quais faixas salariais aparecem nas admissões de TI em Pernambuco, Nordeste e Brasil?",
     "universo": "Admissões (saldo=1), salário válido, ocupações de TI do recorte e geografia selecionada.",
     "colunas": "saldo; salario_valido; salario_real; cbo_codigo; cbo_nome; area_ti; uf_sigla; municipio_nome; competencia",
     "metricas": "p10, p50 e p90 do salário real; número de salários válidos por cargo, área e região.",
     "grafico": "Faixa horizontal p10-p90 com marcador de mediana, por cargo ou área.",
     "justificativa": "Posição em um eixo comum facilita comparação; a faixa mostra dispersão sem reduzir o grupo a uma média.",
     "limites": "Salário de admissão não é salário júnior. Percentis não são mínimo/máximo nem intervalo de confiança."},
    {"id": "P2", "base": "CAGED", "pergunta": "Como se distribuem admissões e desligamentos de TI no primeiro trimestre de 2025?",
     "universo": "Todas as movimentações de TI, inclusive registros com salário sinalizado.",
     "colunas": "saldo; competencia; uf_sigla; area_ti; cbo_familia",
     "metricas": "Contagens de admissões e desligamentos; diferença entre as contagens dos arquivos MOV, por mês e região.",
     "grafico": "Barras agrupadas por área e mês; linha mensal quando a dimensão temporal for o foco.",
     "justificativa": "Comprimentos com origem em zero permitem comparar volumes; meses em ordem preservam a leitura temporal.",
     "limites": "A diferença MOV não é o saldo oficial final ajustado. Três meses não permitem inferir sazonalidade ou tendência longa."},
    {"id": "P3", "base": "CAGED", "pergunta": "Como as distribuições salariais agregadas de admissão e desligamento diferem no mesmo recorte?",
     "universo": "Admissões e desligamentos com salário válido, estratificados pelo mesmo cargo, geografia e competência.",
     "colunas": "movimento; salario_real; salario_valido; cbo_codigo; uf_sigla; competencia",
     "metricas": "p10/p50/p90 por movimento e diferença de medianas, somente quando ambos os grupos têm n>=30.",
     "grafico": "Faixas lado a lado ou boxplots com escala compartilhada.",
     "justificativa": "Alinhamento e escala comum mostram diferenças e sobreposição entre distribuições.",
     "limites": "São grupos distintos. A diferença não mede aumento salarial, promoção ou evolução da mesma pessoa."},
    {"id": "P4", "base": "CAGED", "pergunta": "Que relações aparecem entre salário de admissão, escolaridade, idade, jornada e ocupação?",
     "universo": "Admissões com salário válido; idade/jornada válidas nas análises que usam esses campos.",
     "colunas": "salario_real; escolaridade_grupo; idade; idade_valida; horas_contratuais; horas_validas; cbo_codigo; uf_sigla",
     "metricas": "Distribuições por escolaridade; correlações de Spearman para idade/jornada; diferenças dentro de cargo e UF.",
     "grafico": "Boxplots por escolaridade e dispersão com transparência; agrupamentos exploratórios se justificados.",
     "justificativa": "Boxplots comunicam centro e variação; dispersão revela forma, concentração e observações extremas.",
     "limites": "Idade não representa experiência ou senioridade. Escolaridade é categórica; associações não demonstram causalidade."},
    {"id": "P5", "base": "State of Data", "pergunta": "Quais perfis de formação, vínculo e trabalho aparecem entre iniciantes na área de dados?",
     "universo": "Residentes no Brasil; recortes separados de júnior declarado, estágio e experiência em dados de até dois anos.",
     "colunas": "vive_no_brasil; senioridade_declarada; vinculo_grupo; inicio_carreira_dados_ate_2_anos; escolaridade_grupo; modelo_trabalho; uf_sigla",
     "metricas": "Contagens e proporções por perfil; total elegível, respondido e ausente em cada comparação.",
     "grafico": "Barras horizontais e barras 100% empilhadas com poucas categorias.",
     "justificativa": "Barras permitem comparação precisa; proporções distinguem composição de diferença no tamanho dos grupos.",
     "limites": "Início em dados não significa início em toda a carreira. Esses critérios não devem ser fundidos como equivalentes."},
    {"id": "P6", "base": "State of Data", "pergunta": "Como as faixas salariais declaradas se distribuem por cargo, senioridade e modelo de trabalho?",
     "universo": "Residentes no Brasil com faixa salarial e categoria de comparação respondidas.",
     "colunas": "faixa_salarial_declarada; faixa_salario_limite_inferior; faixa_salario_limite_superior; cargo_atual; senioridade_declarada; modelo_trabalho",
     "metricas": "Proporção de respostas em cada faixa salarial ordenada, por categoria; denominador e faltantes.",
     "grafico": "Barras empilhadas ordenadas ou mapa de calor de proporções com rótulos.",
     "justificativa": "Ordem das faixas preserva a interpretação ordinal; valores e legenda reduzem a dependência da cor.",
     "limites": "Não calcular salário exato ou média usando ponto médio. A faixa superior é aberta; não misturar com salários administrativos."},
    {"id": "P7", "base": "State of Data", "pergunta": "Quais tecnologias são declaradas pelos diferentes perfis da área de dados?",
     "universo": "Residentes no Brasil que responderam ao grupo de tecnologias, estratificados por perfil ou área.",
     "colunas": "respondente_id; area_profissional; senioridade_declarada; usa_sql; usa_python; usa_r; usa_power_bi; usa_aws; usa_gcp; usa_azure",
     "metricas": "Percentual de usuários de cada tecnologia entre respondentes elegíveis que responderam ao item/grupo.",
     "grafico": "Barras horizontais por tecnologia; pequenos múltiplos para comparar perfis.",
     "justificativa": "Comprimento é mais preciso que área para comparar frequência; pequenos múltiplos preservam a mesma escala.",
     "limites": "Múltiplas escolhas podem somar mais de 100%. Ausência não é resposta negativa; opções 'nenhuma' não são tecnologias."},
    {"id": "P8", "base": "State of Data", "pergunta": "Que características se associam à busca ativa por emprego declarada na pesquisa?",
     "universo": "Residentes no Brasil com resposta válida ao item planos_mudar_emprego_6m.",
     "colunas": "planos_mudar_emprego_6m (somente alvo); senioridade_declarada; escolaridade_grupo; vinculo_grupo; modelo_trabalho; experiencia_dados_faixa",
     "metricas": "Proporção de busca ativa, distribuição das classes e avaliação de classificadores contra uma referência simples.",
     "grafico": "Barras de composição e, na etapa 05, matriz de confusão, ROC e precision-recall.",
     "justificativa": "A matriz localiza os erros de cada classe; curvas mostram o efeito do limiar e da composição das classes.",
     "limites": "O alvo é intenção declarada contemporânea, não desligamento futuro. A pergunta do alvo e suas cópias não entram como preditores."},
    {"id": "P9", "base": "Pesquisa G12", "pergunta": "Como os participantes avaliam o acesso à informação e quais dificuldades relatam?",
     "universo": "35 respostas do questionário próprio; cada item usa seu total válido.",
     "colunas": "facilidade_informacao_escala_1_5; dificuldade_principal; curso_graduacao; momento_carreira",
     "metricas": "Distribuição das notas 1 a 5 e contagem/proporção das dificuldades; informar denominadores.",
     "grafico": "Barras ordenadas para notas e barras horizontais para dificuldades.",
     "justificativa": "Ordem preserva a escala ordinal; comprimentos permitem comparar categorias sem atribuir distância psicológica igual às notas.",
     "limites": "As âncoras da escala não estão no XLSX. Não chamar nota alta de facilidade maior antes de confirmar o formulário; não generalizar para todo o mercado."},
    {"id": "P10", "base": "Pesquisa G12", "pergunta": "Que informações os participantes priorizam e que intenção de uso da ferramenta declaram?",
     "universo": "Q08: participantes com seleção reconhecida. Q07: somente respostas Sim/Não válidas.",
     "colunas": "respondente_id; prioridades_quantidade; prioridades_tratamento; opcao_id (tabela prioridades); usaria_ferramenta; usaria_ferramenta_resposta_valida",
     "metricas": "Pessoas que selecionaram cada opção / pessoas que responderam Q08; proporção de Sim em Q07 e total de respostas fora do domínio.",
     "grafico": "Barras horizontais de prioridades; barra de composição para intenção válida.",
     "justificativa": "Comprimento mostra frequência das prioridades; composição usa denominador específico da pergunta, não o número de opções selecionadas.",
     "limites": "Seleções podem somar mais de 100%. Q07 tem três respostas fora do domínio. Intenção declarada em pergunta sobre a solução não comprova adoção ou desejabilidade validada."},
    {"id": "P11", "base": "Pesquisa G12", "pergunta": "Como a expectativa salarial declarada varia com a experiência informada em TI?",
     "universo": "Expectativas não sinalizadas e experiência exata para relações quantitativas; intervalos são analisados separadamente.",
     "colunas": "expectativa_salarial_mensal; expectativa_salarial_revisar; experiencia_ti_meses_exatos; experiencia_ti_meses_min; experiencia_ti_meses_max; momento_carreira",
     "metricas": "Mediana e quartis de expectativa; cobertura de experiência exata e intervalos; associação exploratória somente com n suficiente.",
     "grafico": "Distribuição de expectativas; dispersão apenas em análise interna restrita, agregação em faixas na versão pública.",
     "justificativa": "Distribuição mostra variação sem inventar salário recebido; faixas agregadas reduzem a exposição de perfis individuais na amostra pequena.",
     "limites": "R$5 é sinalizado, não corrigido para R$5.000. Sete a oito meses não viram 7,5. Sem cargo e UF comparáveis, e com coleta em 2026, não medir diferença individual contra CAGED de 2025."},
    {"id": "P12", "base": "Pesquisa G12", "pergunta": "Quantos participantes declaram buscar mudança e quantos cogitaram sair ou mudar de área?",
     "universo": "Respostas válidas de Q10 e Q11, com denominadores separados.",
     "colunas": "busca_mudanca; busca_mudanca_resposta_valida; cogitou_mudar_desistir; cogitou_mudar_desistir_resposta_valida",
     "metricas": "Contagens e proporções de Sim/Não por item; cobertura e respostas inválidas.",
     "grafico": "Barras de composição por pergunta, sem concatenar os dois alvos.",
     "justificativa": "Perguntas separadas mantêm seus significados e permitem ler composição sem sugerir trajetória longitudinal ou causa.",
     "limites": "Q10 abrange emprego, área ou regime; não é o mesmo alvo do State of Data. Cogitar desistir não comprova saída; não treinar classificador com apenas 35 respostas."},
]

VISUAL_OBJECTIVES = {
    "P1": "Comparar remuneração de contratação e dispersão entre ocupações e regiões.",
    "P2": "Mostrar o volume e a composição dos movimentos formais no trimestre.",
    "P3": "Mostrar sobreposição e diferenças entre grupos, sem sugerir evolução individual.",
    "P4": "Explorar associações e variação salarial dentro de recortes comparáveis.",
    "P5": "Caracterizar perfis de entrada na área de dados sem confundir critérios de experiência.",
    "P6": "Comparar a composição das faixas de salário, sem fabricar valores exatos.",
    "P7": "Mostrar tecnologias declaradas por perfil e a cobertura de cada pergunta.",
    "P8": "Comunicar os erros e os limites da classificação de busca ativa declarada.",
    "P9": "Identificar dificuldades de informação na amostra própria para orientar a solução.",
    "P10": "Priorizar conteúdo do painel e distinguir intenção de uso de adoção real.",
    "P11": "Caracterizar expectativas da amostra, preservando limites e privacidade.",
    "P12": "Descrever intenções distintas de mudança, sem apresentar causa ou previsão.",
}
for question in QUESTIONS:
    question["objetivo_visual"] = VISUAL_OBJECTIVES[question["id"]]

CRITERIA = [
    ("CC01", "Plano de análise", "01_plano_de_analise", "Perguntas, fontes, métricas, objetivos visuais e justificativas dos gráficos", "Completo documentalmente; revisado com pesquisa G12"),
    ("CC02", "Plano de preparação", "02_preparacao_dados", "Fontes, formatos e justificativas de limpeza, normalização e transformação", "Concluido com pipeline validado e alertas documentados"),
    ("CC03", "Análise exploratória", "03_analise_exploratoria", "Notebook com distribuições, relações, agrupamentos e interpretação", "Executada com notebook e interpretacoes; pesquisa propria restrita"),
    ("CC04", "Regressão", "04_regressao", "Notebook com dispersão, tendência e resíduos", "Executada com teste temporal e referencia de mediana; limites documentados"),
    ("CC05", "Classificação", "05_classificacao", "Matriz de confusão, métricas, ROC e precision-recall interpretadas", "Executada com validacao no treino e teste separado; desempenho limitado interpretado"),
    ("CC06", "Dashboard inicial", "06_dashboard_e_publicacao", "Visualizações integradas, filtros e narrativa visual", "V1 local implementada com testes e evidencias; hospedagem externa nao realizada"),
    ("CC07", "Proposta de integração web", "06_dashboard_e_publicacao", "Estrutura das páginas, organização visual e ferramenta de publicação", "Proposta documentada em Streamlit; implantacao externa pendente"),
    ("CC08", "Dashboard consolidado", "07_consolidacao_e_validacao", "Dados, visualizações e textos finalizados; melhorias por feedback", "V1.1 consolidada tecnicamente; feedback estruturado do grupo pendente"),
    ("CC09", "Versão quase final", "07_consolidacao_e_validacao", "Avaliação funcional e ajustes finais", "Validada tecnicamente no ambiente local; revisao do grupo e remota pendentes"),
    ("CC10", "Documentação final", "08_documentacao_final", "Histórico, capturas/links e síntese dos insights", "Concluida em PDF e Markdown com evidencias e limitacoes; revisao do grupo e hospedagem pendentes"),
]


def br(value):
    return f"{value:,}".replace(",", ".")


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def pages(inventory):
    cg, sd = inventory["caged"], inventory["state_of_data"]
    own = json.loads((DATA / "fontes_pesquisa_grupo12.json").read_text(encoding="utf-8"))
    group, desk = own["questionario"], own["matriz"]
    blocks1 = [
        ("p", "<b>Objetivo:</b> planejar análises que ajudem estudantes e profissionais iniciantes a compreender salários de contratação, movimentações do emprego formal e perfis da área de dados, com foco em Pernambuco e Nordeste."),
        ("h", "Problema e público"),
        ("p", "A hipótese de problema é que informações sobre o mercado de TI são fragmentadas e difíceis de comparar. O Radar pretende apoiar decisões de carreira. O grupo forneceu um questionário com 35 respostas, de estudantes de CC e Design; seus resultados ainda devem ser analisados e não são validação automática da hipótese."),
        ("h", "Pergunta central"),
        ("p", "Quais salários e fluxos aparecem no emprego formal de TI, que perfis são declarados na área de dados e quais dificuldades, prioridades e intenções os participantes da pesquisa própria relatam?"),
        ("table", [["Fonte e unidade", "Recorte disponível", "Uso previsto"],
            ["Novo CAGED: movimentação de admissão ou desligamento", "Jan-mar/2025. Brasil: " + br(cg["registros_ti"]) + "; Nordeste: " + br(cg["registros_nordeste"]) + "; PE: " + br(cg["registros_pe"]) + ".", "Faixas salariais e fluxos de emprego formal."],
            ["State of Data: resposta de participante", "2024-2025. " + br(sd["respondentes"]) + " respostas tratadas; " + br(5076) + " residentes no Brasil; PE: 120.", "Perfis, formação, tecnologias e intenção de mudança."],
            ["Pesquisa G12: resposta ao questionário próprio", br(group["registros"]) + " respostas; 12 perguntas; coleta de 31/08 a 04/09/2026.", "Necessidades, prioridades, expectativa e intenção de mudança."],
            ["IPCA e municípios do IBGE", "IPCA jan-mar/2025, referência mar/2025; códigos municipais padronizados.", "Comparabilidade monetária e geográfica."]]),
        ("h", "Escopo do pacote"),
        ("p", "O CAGED foi filtrado pelas famílias 1236, 1425, 2122, 2123, 2124, 3171 e 3172, totalizando 27 ocupações. O agrupamento analítico de áreas está em <b>datasets/auxiliares/cbo_ti_categorias.csv</b>. Os números acima são inventário do pacote, não resultados das análises planejadas."),
        ("p", "As fontes permanecem separadas, com catálogo único. A matriz G12 contém 21 referências/hipóteses, não microdados. RAIS, PNAD, INEP, Brasscom e Exame são referências da matriz, não bases importadas neste pacote. O CAGED disponível não corresponde ao ano inteiro nem ao mercado atual de 2026."),
    ]
    def question_blocks(base):
        blocks = []
        for q in QUESTIONS:
            if q["base"] != base:
                continue
            blocks += [("h", q["id"] + " " + q["pergunta"]),
                       ("p", "<b>Universo:</b> " + q["universo"]),
                       ("p", "<b>Métricas:</b> " + q["metricas"]),
                       ("p", "<b>Visualização:</b> " + q["grafico"]),
                       ("p", "<b>Limite de interpretação:</b> " + q["limites"])]
        return blocks
    return [
        ("Plano de análise de carreiras", "Escopo, fontes e objetivos", blocks1),
        ("Emprego formal em TI", "Perguntas P1 a P4 para o Novo CAGED", question_blocks("CAGED")),
        ("Carreira na área de dados", "Perguntas P5 a P8 para o State of Data Brazil", question_blocks("State of Data")),
        ("Pesquisa própria do Grupo 12", "Perguntas P9 a P12 para necessidades e intenções", question_blocks("Pesquisa G12")),
        ("Métricas e regras de leitura", "Definições para assegurar comparações consistentes", [
            ("table", [["Métrica", "Definição e regra"],
                ["Faixa salarial real", "p10/p50/p90 dos salários mensais válidos. p50 é a mediana; p10/p90 não são extremos nem confiança estatística."],
                ["Correção monetária", "salario_real = salario_nominal × IPCA(mar/2025) / IPCA(competência). Unidade: reais por mês a preços de mar/2025."],
                ["Volume e diferença MOV", "Admissões = contagem de saldo=1; desligamentos = contagem de saldo=-1. Diferença MOV = admissões - desligamentos no arquivo selecionado."],
                ["Participação em uma categoria", "Respostas da categoria / respostas válidas do item no universo selecionado. Mostrar denominador e quantidade ausente."],
                ["Tecnologia declarada", "Respostas True / (True + False) do item entre elegíveis. Não transformar ausente em False; itens de múltipla escolha podem exceder 100% em conjunto."],
                ["Correlação exploratória", "Spearman para variáveis quantitativas observadas. Não atribuir ordem numérica arbitrária a UF, cargo ou escolaridade."],
                ["Dados insuficientes", "Comparações estatísticas: n>=30 por grupo, regra operacional de estabilidade, não garantia de representatividade. Pesquisa G12: descrever o total e não fazer inferência de subgrupos pequenos."]]),
            ("h", "Elegibilidade e qualidade"),
            ("p", "O pacote sinaliza " + br(cg["salarios_sinalizados"]) + " salários nominais fora do intervalo plausível de R$300 a R$200.000 ou inválidos. Eles permanecem nos dados e nas contagens de movimentações, mas não compõem as estatísticas salariais. Usar idade_valida e horas_validas quando essas variáveis forem analisadas."),
            ("p", "No State of Data foram retiradas duas linhas exatamente repetidas. As linhas iguais do CAGED foram preservadas porque podem representar eventos distintos. Valores ausentes e respostas não aplicáveis serão informados com denominadores específicos; não haverá imputação automática na análise descritiva."),
            ("p", "No G12 nenhuma linha foi removida. Q07 tem três respostas fora de Sim/Não, mantidas no original e excluídas da proporção válida. Uma expectativa salarial requer revisão. Um intervalo de experiência não vira valor exato. As âncoras de Q05 precisam ser confirmadas."),
            ("h", "Limites das fontes"),
            ("p", "CAGEDMOV cobre o emprego formal e não identifica pessoas, tempo de vínculo, senioridade ou habilidades. Não inclui neste pacote os ajustes FOR/EXC. A pesquisa é voluntária, autodeclarada e específica da área de dados. Faixas abertas de salário não serão convertidas em remuneração pontual. Três meses não sustentam previsão de longo prazo."),
        ]),
        ("Visualizações e comunicação", "Objetivos visuais e princípios de percepção", [
            ("table", [["Pergunta e gráfico", "Objetivo da comunicação", "Justificativa visual"],
                *[[q["id"] + ": " + q["grafico"], q["objetivo_visual"], q["justificativa"]] for q in QUESTIONS if q["base"] != "Pesquisa G12"]]),
            ("h", "Apresentação no Radar"),
            ("p", "Priorizar visão geral de Pernambuco, ampliar para Nordeste e Brasil e permitir detalhe por cargo/área e período. Separar as páginas de emprego formal e perfis da área de dados. Usar a identidade visual já definida em app/theme.py: contraste, uma cor de destaque, rótulos diretos e escala comum nas comparações."),
            ("p", "Toda visualização informará fonte, período, unidade, universo, n válido e exclusões relevantes. Barras partem de zero; eixos não serão truncados de forma enganosa. Cores não serão o único meio de distinguir séries. Recortes vazios ou insuficientes terão mensagem explícita."),
        ]),
        ("Comunicação da pesquisa própria", "Objetivos visuais, integração e privacidade", [
            ("table", [["Pergunta e gráfico", "Objetivo da comunicação", "Justificativa visual"],
                *[[q["id"] + ": " + q["grafico"], q["objetivo_visual"], q["justificativa"]] for q in QUESTIONS if q["base"] == "Pesquisa G12"]]),
            ("h", "Integração sem mistura de populações"),
            ("p", "O dashboard terá seções separadas de emprego formal, perfis em dados e pesquisa do grupo. Aproximar temas, não juntar pessoas. Expectativa salarial de 2026, salário formal de 2025 e faixas da pesquisa nacional não são uma única variável. Q10 do G12 e busca ativa do State of Data têm significados diferentes."),
            ("h", "Publicação responsável"),
            ("p", "Originais e respostas individuais G12 ficam locais e ignorados pelo Git. IDs novos são pseudônimos de linha, não garantia de anonimização. O horário exato da coleta não entra nas tabelas analíticas. Consentimento para divulgação não está documentado no XLSX e deve ser confirmado antes de publicar."),
            ("p", "Evitar cruzamentos raros, pontos individuais e respostas brutas na versão pública. Agregar e avaliar risco de reidentificação; suprimir células com menos de cinco respostas e, quando necessário, células complementares. Essa regra não substitui revisão de privacidade ou autorização dos participantes."),
        ]),
        ("Modelagem e avaliação", "Protocolos previstos para as etapas 04 e 05", [
            ("h", "Regressão para salário de admissão"),
            ("p", "Universo: admissões de TI com salario_valido=True. Alvo: salario_real. Entradas candidatas: cargo/CBO, UF, escolaridade, idade e jornada. Começar com um modelo linear simples e comparar com uma referência que prevê a mediana do treino. Relacionar diferenças por cargo e UF antes de interpretar coeficientes."),
            ("p", "Treino inicial: janeiro e fevereiro de 2025. Avaliação final: março de 2025, reservado antes do ajuste. Escalas, imputação e codificação de categorias serão ajustadas apenas no treino. Não usar salario_nominal, salario_fixo_declarado, faixa_salario_real, escalas do alvo ou registros de origem como preditores."),
            ("p", "Entregar MAE/RMSE, observados versus previstos, dispersão com tendência e resíduos versus previsão. Verificar desempenho por UF/área quando houver registros suficientes. Os modelos representam relações no recorte e não acompanham a evolução da mesma pessoa."),
            ("h", "Classificação de busca ativa por emprego"),
            ("p", "Universo: residentes no Brasil com planos_mudar_emprego_6m respondido. Há 4.734 respostas elegíveis: 1.630 em busca ativa e 3.104 sem busca ativa. Estes totais caracterizam o alvo disponível; o desempenho do modelo ainda será medido."),
            ("table", [["Classe", "Regra baseada na resposta original"],
                ["1 - Busca ativa", "Estou em busca de oportunidades dentro ou fora do Brasil; ou estou em busca de oportunidades, mas apenas fora do Brasil."],
                ["0 - Sem busca ativa", "Não estou buscando, mas me considero aberto a outras oportunidades; ou não estou buscando e não pretendo mudar de emprego nos próximos 6 meses."],
                ["Ausente", "Excluir da tarefa supervisionada; não converter em classe 0."]]),
            ("p", "Entradas iniciais: senioridade declarada, formação, vínculo, modelo de trabalho e experiência em dados. Excluir a pergunta-alvo e cópias no arquivo completo; na primeira versão, também excluir entrevistas recentes, oportunidades buscadas e tempo de busca, que podem aproximar diretamente a resposta."),
            ("p", "Separar treino/teste estratificados, 80%/20%, com semente fixa 12. Comparar referência de classe majoritária, regressão logística e árvore simples. Ajustar pré-processamento e limiar com o treino, sem consultar o teste. Entregar matriz de confusão, acurácia, precisão, recall, F1, ROC e precision-recall; explicitar a classe positiva e o limiar."),
        ]),
        ("Execução e critérios de aceite", "Rastreabilidade da etapa 01 e próximos passos", [
            ("h", "Critérios da etapa 01"),
            ("table", [["Critério", "Evidência neste plano"],
                ["Dados que serão utilizados", "Fontes, recortes e unidades na seção de escopo e no catálogo; registro distingue dados importados e referências."],
                ["Perguntas de análise", "P1 a P12, com universo, colunas e limites. Matriz CSV acompanha o documento."],
                ["Métricas previstas", "Quantis, contagens, proporções, relações e avaliação definidos nas perguntas, regras e protocolos."],
                ["Objetivos da comunicação visual", "Objetivo explícito por pergunta nas duas seções de visualizações e na matriz CSV."],
                ["Justificativa dos gráficos", "Posição, comprimento, distribuição, ordem, contraste, escala e privacidade fundamentam as escolhas."]]),
            ("h", "Sequência de execução"),
            ("p", "Concluir o plano de preparação (02). Executar P1 a P12 na exploração (03), verificando domínio de Q07, expectativa sinalizada, escala Q05 e protocolo de recrutamento. Desenvolver regressão (04) e classificação (05) com as bases adequadas, não com a pequena amostra G12. Implementar dashboard/publicação (06), validar (07) e documentar (08)."),
            ("p", "A elaboração deste plano não conclui a análise exploratória, modelos ou validação com usuários. Os artefatos do ciclo anterior continuam preservados na raiz do projeto e serão tratados como histórico do recorte anterior."),
            ("h", "Referências e procedência"),
            ("p", "<b>Critérios:</b> Entregáveis 5ºP - Projeto 2026.1-2, coluna CC Análise e Visualização de Dados, copiado para 00_referencias/criterios_avd_cc.pdf."),
            ("p", '<b>MTE:</b> <link href="https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged">Microdados RAIS e CAGED</link>. Originais e layout em datasets/brutos.'),
            ("p", '<b>Data Hackers:</b> <link href="https://www.kaggle.com/datasets/datahackers/state-of-data-brazil-20242025">State of Data Brazil 2024-2025</link>; arquivo obtido do espelho público da comunidade, registrado no manifesto.'),
            ("p", '<b>IBGE:</b> <link href="https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/202501-202503">IPCA SIDRA, tabela 1737 e variável 2266</link>; <link href="https://servicodados.ibge.gov.br/api/v1/localidades/municipios">API de Localidades</link> para municípios.'),
            ("p", "<b>Reprodução:</b> datasets/fontes_manifesto.json, auxiliares/dicionario_dados.csv, qualidade/relatorio_qualidade.json e qualidade/validacao_exports.json. Os arquivos brutos têm hashes SHA-256 registrados."),
            ("p", "<b>Grupo 12:</b> questionário e matriz XLSX fornecidos pelo grupo. Manifesto próprio, mapa de perguntas, relatório de qualidade e script prepare_grupo12.py preservam sua procedência. A fase 01 atende documentalmente aos cinco critérios; isso não representa aprovação da professora ou conclusão das fases seguintes."),
        ]),
    ]


def markdown_text(text):
    text = re.sub(r'<link href="([^"]+)">(.*?)</link>', r'[\2](\1)', text)
    return text.replace("<b>", "**").replace("</b>", "**")


def render_plan(pages_content, repo):
    spec = importlib.util.spec_from_file_location("radar_theme", repo / "app" / "theme.py")
    theme = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(theme)
    ink = colors.HexColor(theme.TEXTO)
    muted = colors.HexColor(theme.TEXTO_SECUNDARIO)
    shade = colors.HexColor(theme.CINZA_CLARO)
    border = colors.HexColor(theme.BORDA_CLARA)
    font = "Helvetica"
    bold = "Helvetica-Bold"
    arial = Path("C:/Windows/Fonts/arial.ttf")
    if arial.exists():
        pdfmetrics.registerFont(TTFont("PlanArial", str(arial)))
        pdfmetrics.registerFont(TTFont("PlanArialBold", "C:/Windows/Fonts/arialbd.ttf"))
        pdfmetrics.registerFontFamily("PlanArial", normal="PlanArial", bold="PlanArialBold")
        font, bold = "PlanArial", "PlanArialBold"
    styles = {
        "title": ParagraphStyle("Title", fontName=bold, fontSize=22, leading=26, textColor=ink, spaceAfter=5),
        "sub": ParagraphStyle("Subtitle", fontName=font, fontSize=10, leading=14, textColor=muted, spaceAfter=15),
        "h": ParagraphStyle("Heading", fontName=bold, fontSize=11.4, leading=15, textColor=ink, spaceBefore=10, spaceAfter=5, keepWithNext=True),
        "p": ParagraphStyle("Body", fontName=font, fontSize=10.15, leading=14.1, textColor=ink, spaceAfter=6),
        "cell": ParagraphStyle("Table", fontName=font, fontSize=9.15, leading=12.5, textColor=ink),
        "head": ParagraphStyle("TableHead", fontName=bold, fontSize=9.15, leading=12.5, textColor=colors.white),
    }
    width = A4[0] - 84
    content = []
    for index, (title, subtitle, blocks) in enumerate(pages_content):
        if index:
            content.append(PageBreak())
        content += [Paragraph(title, styles["title"]), Paragraph(subtitle, styles["sub"])]
        if not index:
            content.insert(2, Paragraph("Radar de Carreira em TI - Grupo 12 - CESAR School<br/>Etapa 01 - Versão 1.1 - 14 de outubro de 2026", styles["sub"]))
        for kind, value in blocks:
            if kind != "table":
                content.append(Paragraph(value, styles[kind]))
                continue
            count = len(value[0])
            cols = [width * .30, width * .70] if count == 2 else [width * .32, width * .34, width * .34]
            items = [[Paragraph(str(cell), styles["head"] if i == 0 else styles["cell"]) for cell in row] for i, row in enumerate(value)]
            table = Table(items, colWidths=cols, hAlign="LEFT", repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(theme.GRAFITE)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, -1), .4, border),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, shade]),
            ]))
            content += [table, Spacer(1, 8)]
    total = len(pages_content)
    def footer(canvas, doc):
        canvas.setFont(font, 8)
        canvas.setFillColor(muted)
        canvas.drawString(42, 25, "Radar de Carreira em TI - Plano de análise")
        canvas.drawRightString(A4[0] - 42, 25, f"{doc.page} / {total}")
    doc = SimpleDocTemplate(str(OUT / "plano_de_analise.pdf"), pagesize=A4, leftMargin=42, rightMargin=42,
                            topMargin=36, bottomMargin=45, title="Plano de análise de carreiras", author="Grupo 12")
    doc.build(content, onFirstPage=footer, onLaterPages=footer)
    reader = PdfReader(OUT / "plano_de_analise.pdf")
    if len(reader.pages) != total:
        raise ValueError(f"Layout overflow: {len(reader.pages)} pages, expected {total}")
    extracted = " ".join(" ".join(page.extract_text().split()) for page in reader.pages)
    for term in ("P1", "P12", "IPCA", "precision-recall", "Critérios da etapa 01", "Treino inicial", "Pesquisa G12"):
        assert term in extracted, term


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    inventory = json.loads((DATA / "qualidade" / "relatorio_qualidade.json").read_text(encoding="utf-8"))
    body = pages(inventory)
    md = ["# Plano de análise de carreiras", "", "Radar de Carreira em TI. Grupo 12. CESAR School.",
          "Etapa 01. Versão 1.1. 14 de outubro de 2026.", ""]
    for i, (title, subtitle, blocks) in enumerate(body):
        md += [f"## {i + 1} {subtitle}", ""]
        for kind, value in blocks:
            if kind == "h":
                md += ["### " + value, ""]
            elif kind == "p":
                md += [markdown_text(value), ""]
            else:
                md += ["| " + " | ".join(markdown_text(str(c)) for c in value[0]) + " |",
                       "| " + " | ".join("---" for _ in value[0]) + " |"]
                md += ["| " + " | ".join(markdown_text(str(c)) for c in row) + " |" for row in value[1:]]
                md.append("")
    (OUT / "plano_de_analise.md").write_text("\n".join(md), encoding="utf-8")
    write_csv(OUT / "matriz_perguntas_metricas.csv", list(QUESTIONS[0]), QUESTIONS)
    write_csv(ROOT / "00_referencias" / "matriz_criterios.csv",
              ["id", "entregavel", "pasta", "evidencia_esperada", "situacao"],
              [dict(zip(["id", "entregavel", "pasta", "evidencia_esperada", "situacao"], row)) for row in CRITERIA])
    render_plan(body, args.repo)
    print("Analysis plan exported: PDF, Markdown and traceability matrices.")


if __name__ == "__main__":
    main()
