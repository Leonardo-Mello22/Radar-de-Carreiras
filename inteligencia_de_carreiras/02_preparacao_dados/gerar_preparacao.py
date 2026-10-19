"""Build the preparation plan, column-level decisions and acceptance evidence."""
from __future__ import annotations

import argparse
import csv
import importlib.metadata
import importlib.util
import json
import re
from html import escape
from pathlib import Path

import pandas as pd
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

AREA = Path(__file__).resolve().parents[1]
OUT, DATA = AREA / "02_preparacao_dados", AREA / "datasets"


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def rule(dataset, column, dtype):
    """Return operation, missing-value policy, rationale and analysis linkage."""
    preserve = "Preservar ausentes; não imputar na descrição."
    if column in ("registro_id", "respondente_id", "linha_origem", "referencia_id", "fonte", "arquivo_origem"):
        return ("Preservar ID de linha e procedência; excluir como preditor.", "Ausência de ID/procedência bloqueia a validação.",
                "Permite reconciliação sem afirmar identidade longitudinal de pessoas.", "Rastreabilidade de P1-P12")
    if dataset == "caged_ti":
        if column in ("salario_nominal", "salario_fixo_declarado", "salario_real", "salario_valido", "salario_status", "faixa_salario_real", "mes_referencia_ipca"):
            return ("Ler números brasileiros; salário mensal sem converter por horas; corrigir IPCA para mar/2025; sinalizar nominal fora de [300,200000]; criar faixas [a,b).",
                    "Salário ausente/inválido permanece; não compõe estatísticas de salário, mas conta movimentação.",
                    "Comparar remuneração em poder de compra comum sem fabricar salário, eliminar movimentos ou confundir parte fixa com mensal.", "P1, P3, P4; alvo da regressão")
        if "salario" in column:
            return ("Preservar código/texto da unidade da parte fixa e traduzir pelo layout.", preserve,
                    "A unidade do componente fixo não muda o salário mensal do campo salario.", "P1, P3, P4")
        if column in ("idade", "idade_valida", "faixa_etaria"):
            return ("Inteiro original; sinalizar fora de [14,90]; faixas 14-17/18-24/25-34/35-44/45-54/55-64/65-90.",
                    "Inválido preservado na base, ausente em escalas; faixa não informada/inválida.",
                    "Evitar relações e escalas dominadas por idade impossível; idade não equivale a experiência.", "P4")
        if column in ("horas_contratuais", "horas_validas", "jornada_grupo"):
            return ("Número de horas; validade [1,48]; grupos (0,20], (20,30], (30,40], (40,44], (44,48].",
                    "Inválido preservado, excluído de relações que usam jornada e de suas escalas.",
                    "Comparar jornadas sem apagar eventos; limites são operacionais, não avaliação legal de contratos.", "P4")
        if column.startswith("cbo_") or column in ("area_ti", "funcao_gestao"):
            return ("CBO de seis dígitos como texto; filtrar sete famílias; tradução oficial e agrupamento analítico por código exato.",
                    "Código sem tradução/categoria requer revisão; o pacote exige correspondência completa.",
                    "Preservar zeros e delimitar 27 ocupações coerentes com o escopo; área é derivação, não taxonomia oficial de toda TI.", "P1-P4")
        if column in ("saldo", "movimento", "tipo_movimentacao", "tipo_movimentacao_cod", "primeiro_emprego_formal"):
            return ("saldo 1=admissão e -1=desligamento; traduzir tipo; primeiro emprego deriva de código 10.",
                    "Movimento não reconhecido bloqueia; nunca inferir júnior por primeiro emprego.",
                    "Contagens e grupos salariais dependem da natureza do evento; não são vagas anunciadas ou pessoas únicas.", "P1-P4")
        if column.startswith(("uf_", "municipio_")) or column in ("regiao_nome", "recorte_regional"):
            return ("Códigos em texto; município CAGED de seis dígitos ligado unicamente ao IBGE de sete; UFs e recortes regionais.",
                    "Geografia não traduzida requer revisão; não preencher município por aproximação.",
                    "Garantir chave única e filtros territoriais corretos; PE é subconjunto de Nordeste e Brasil.", "P1-P4")
        if column in ("competencia", "ano", "mes", "trimestre", "data_competencia", "competencia_declaracao", "declaracao_fora_prazo", "origem_informacao_cod"):
            return ("Competência YYYYMM em texto; derivar calendário e preservar competência de declaração, prazo e origem.",
                    "Competência inválida ou sem IPCA bloqueia o cálculo.",
                    "Separar data do movimento de declaração; não chamar MOV de saldo final ajustado ou série anual.", "P1-P4")
        if column in ("grau_instrucao", "grau_instrucao_cod", "escolaridade_grupo"):
            return ("Manter grau oficial e agrupamento educacional explícito.", "Usar não informado como categoria de cobertura, não como escolaridade zero.",
                    "Escolaridade é categórica e não tem distância numérica arbitrária; ordenar com sentido educacional apenas nos gráficos.", "P4")
        return ("Preservar código oficial e sua descrição, ou booleano 0/1 anulável; não fundir desconhecido com falso.", preserve,
                "Manter contexto de vínculo, estabelecimento e perfil sem converter atributos nominais em números de ordem.", "P1-P4; filtros e cobertura")
    if dataset == "state_of_data_carreiras":
        if column == "atua_como_gestor" or column in ("cargo_gestao", "cargo_atual", "area_profissional"):
            return ("Converter indicador explícito True/False para booleano anulável; cargo original preservado; gestor sem cargo técnico recebe área Gestao.",
                    "Cargo pode estar ausente por ramificação do questionário; não preencher com senioridade.",
                    "Corrigir comparação texto/booleano e respeitar perguntas condicionais; área é agrupamento documentado.", "P5-P7")
        if "salario" in column or column == "remuneracao_medida":
            return ("Preservar intervalo declarado, extrair limites e indicar inclusividade; teto permanece ausente em faixa aberta.",
                    "Distinguir não respondido de limite superior aberto; não usar ponto médio ou salário exato.",
                    "Faixa ordinal não determina remuneração individual precisa e não é salário administrativo do CAGED.", "P6")
        if column in ("idade", "idade_valida", "faixa_etaria"):
            return ("Idade observada com validade [14,90] e faixas do pacote.", preserve,
                    "Controlar cobertura sem usar idade como experiência/senioridade.", "P5; controle descritivo")
        if column.startswith("usa_"):
            return ("Alternativa de tecnologia como booleano anulável; tabela longa inclui apenas seleções verdadeiras.",
                    "Ausente não vira False. Percentual exige elegíveis com resposta no item.",
                    "Pergunta de múltipla escolha não tem como denominador o número de seleções nem todos os entrevistados indistintamente.", "P7")
        if column in ("senioridade_declarada", "experiencia_dados_faixa", "experiencia_ti_anterior_faixa", "inicio_carreira_dados_ate_2_anos"):
            return ("Manter nível declarado e faixas de experiência; indicador até dois anos usa apenas experiência em dados.", preserve,
                    "Início em dados, nível declarado e experiência anterior em TI são conceitos diferentes; não imputar júnior.", "P5, P6, P8")
        if column in ("planos_mudar_emprego_6m", "participou_entrevistas_6m", "oportunidade_buscada", "tempo_busca_oportunidade", "objetivo_carreira"):
            return ("Preservar respostas e contexto; item de planos usado apenas como alvo na classificação; excluir proxies próximos do alvo.",
                    "Alvo ausente não vira negativo; perguntas condicionais não preenchidas permanecem ausentes.",
                    "Evitar vazamento e confusão entre intenção atual e desligamento futuro.", "P8")
        if column in ("vive_no_brasil", "pais_residencia", "uf_sigla", "regiao_nome", "recorte_regional"):
            return ("UF em maiúsculas; Brasil deriva da resposta de residência; exterior explícito; recortes por UF.", preserve,
                    "Manter população geográfica coerente; não transformar ausência de UF em Pernambuco.", "P5-P8")
        if column in ("situacao_trabalho", "vinculo_grupo", "modelo_trabalho_declarado", "modelo_trabalho", "modelo_trabalho_ideal"):
            return ("Preservar declaração e criar categorias de vínculo e trabalho por mapeamento explícito.",
                    "Não informado separado de remoto/presencial e emprego/desemprego.",
                    "Reduzir categorias para comparação sem apagar conceitos do questionário.", "P5, P6, P8")
        if column in ("nivel_ensino", "area_formacao", "escolaridade_grupo"):
            return ("Preservar formação; agrupar nível de ensino sem escala numérica arbitrária.", preserve,
                    "Comparar perfis educacionais mantendo a distinção entre ausência e formação informada.", "P5, P8")
        return ("Normalizar texto/tipo conservando a resposta; manter detalhes disponíveis na base completa.", preserve,
                "Contexto de perfil não autoriza inferir vínculo, carreira total ou valores não observados.", "P5-P8; controle de cobertura")
    if dataset.startswith("pesquisa_grupo12"):
        if "prioridade" in column or column in ("opcao", "opcao_id"):
            return ("Reconhecer sete alternativas completas; criar uma linha por seleção Q08; validar de uma a três escolhas.",
                    "Seleção desconhecida é sinalizada; não dividir vírgulas internas das opções.",
                    "O denominador é participantes do item, não 101 seleções; várias opções podem exceder 100%.", "P10")
        if "expectativa" in column:
            return ("Preservar número original; inteiro mensal e flag fora de [300,200000] ou não parseável; R$5 não vira R$5000.",
                    "Sinalizado fica disponível para revisão e sensibilidade; filtro explícito nas estatísticas.",
                    "Expectativa não é remuneração recebida; limite de revisão operacional, não verdade sobre o respondente.", "P11")
        if "experiencia" in column:
            return ("Meses numéricos ou anos/meses inequívocos; intervalo guarda limites; exato ausente quando min!=max.",
                    "Texto ambíguo sinalizado; zero meses é válido.",
                    "Não inventar experiência pontual por média de um intervalo declarado.", "P11")
        if "usaria_ferramenta" in column:
            return ("Preservar Q07 original; converter somente Sim/Não; indicador de validade e três respostas fora do domínio.",
                    "Booleano ausente fora do domínio; proporção usa as 32 respostas válidas.",
                    "Não deslocar respostas de outra semântica nem apresentar intenção como adoção real.", "P10")
        if "busca_mudanca" in column or "cogitou" in column:
            return ("Preservar declaração e converter Sim/Não com flag de validade.", preserve,
                    "Q10 mistura emprego/área/regime; Q11 relata cogitação, não saída. Não fundir com alvo State of Data.", "P12")
        if "facilidade" in column:
            return ("Inteiro ordinal 1 a 5; validar domínio, sem inferir direção da escala.", preserve,
                    "Âncoras não estão no XLSX; apenas distribuição de notas antes de confirmação.", "P9")
        if "periodo" in column:
            return ("Preservar texto e extrair número quando explícito; desperiodizado não vira zero.", preserve,
                    "Período acadêmico não mede experiência profissional nem senioridade.", "P9-P12; contexto da amostra")
        if column in ("pergunta_id", "campo", "resposta"):
            return ("Reformatar 12 perguntas em tabela longa ligada por ID de linha e pergunta; manter resposta normalizada.", preserve,
                    "420 linhas continuam representando 35 respostas ao formulário, não 420 participantes.", "P9-P12")
        return ("Texto NFC e espaços normalizados; ordenar perguntas por número; carimbo exato não entra no analítico.", preserve,
                "Manter contexto e privacidade; 35 respostas não sustentam representatividade do mercado ou treino de classificador.", "P9-P12")
    if dataset == "matriz_pesquisa_grupo12":
        return ("Preservar achados, CSD, confiança e datas declarados; extrair hyperlinks e adicionar alerta metodológico.", preserve,
                "Referência/hipótese não é microdado nem evidência checada; confiança declarada não passa a validação externa.", "Contexto e hipóteses de P1-P12")
    if dataset == "state_of_data_completo_normalizado":
        return ("Nome q_ + snake_case único; texto NFC; números inteiros/reais com tipos anuláveis; booleanos explícitos e alternativas 0/1 numéricas preservam nulos.", preserve,
                "Normalização de formato mantém 403 perguntas originais sem inventar respostas; aliases analíticos seguem regras específicas.", "Consulta de origem para P5-P8; seleção de preditores deve excluir alvos/proxies")
    if dataset == "cbo_ti_categorias" and column == "area_ti":
        return ("Mapear cada CBO selecionada ao agrupamento analítico documentado no código.", "Categoria não mapeada exige revisão.",
                "A descrição de CBO é oficial, mas área de TI é classificação do projeto, não taxonomia oficial.", "P1-P4")
    return ("Manter dimensão oficial e chave única; converter índices para número e códigos para texto.", "Ausência de chave ou fator necessário bloqueia enriquecimento.",
            "Impedir multiplicação de linhas nas ligações e garantir tradução/correção monetária rastreável.", "Apoio a P1-P4")


def column_matrix():
    names = ["caged_ti", "state_of_data_carreiras", "state_of_data_completo_normalizado",
             "pesquisa_grupo12_respostas", "pesquisa_grupo12_respostas_longas", "pesquisa_grupo12_prioridades",
             "matriz_pesquisa_grupo12"]
    rows = []
    for folder, datasets in [("tratados", names), ("auxiliares", ["municipios_ibge", "ipca_deflatores", "cbo_ti_categorias"])]:
        for name in datasets:
            frame = pd.read_parquet(DATA / folder / f"{name}.parquet")
            for column in frame:
                operation, missing, rationale, linkage = rule(name, column, str(frame[column].dtype))
                rows.append({"dataset": name, "coluna": column, "tipo_tratado": str(frame[column].dtype),
                             "nulos_observados": int(frame[column].isna().sum()), "tratamento": operation,
                             "politica_nulos": missing, "justificativa": rationale, "perguntas_fase01": linkage})
    write_csv(OUT / "matriz_preprocessamento.csv", rows)
    return rows


def br(value):
    return f"{value:,}".replace(",", ".")


def document_content(report, own, execution, matrix):
    c, s, g = report["caged"], report["state_of_data"], own["questionario"]
    versions = ", ".join(f"{k} {v}" for k, v in execution["dependencias"].items())
    return [
        ("Preparação dos dados", "Etapa 02 - Plano, justificativas e execução", [
            ("p", "<b>Radar de Carreira em TI - Grupo 12 - CESAR School</b><br/>Versão 1.0 - 14 de outubro de 2026"),
            ("p", "<b>Objetivo:</b> tornar as fontes adequadas às perguntas P1-P12 da fase 01, mantendo origem, unidade de observação, significado das variáveis e limitações. A etapa entrega o plano e um pipeline executado, não resultados de exploração ou modelos."),
            ("table", [["Fonte e formato bruto", "Recorte tratado", "Uso e justificativa"],
                ["Novo CAGED: três .7z com texto UTF-8 separado por ;. Layout oficial XLSX.", "Jan-mar/2025: " + br(c["registros_ti"]) + " movimentos, 62 campos; PE e Nordeste como subconjuntos.", "Emprego formal e salário mensal. Famílias CBO delimitam ocupações do Radar."],
                ["State of Data: ZIP com CSV, 403 campos originais.", br(s["respondentes"]) + " respostas; base de carreiras com 51 campos.", "Perfis em dados, faixas de salário e busca declarada; pesquisa voluntária."],
                ["Grupo 12: questionário XLSX e matriz XLSX.", "35 respostas/12 perguntas; 21 referências e hipóteses.", "Necessidades e intenções; matriz é contexto, não amostra de trabalhadores."],
                ["IBGE: municípios e IPCA em JSON.", "5.571 municípios; três índices/fatores de IPCA.", "Tradução territorial e salários a preços de mar/2025."]]),
            ("h", "Saídas e procedência"),
            ("p", "CSV UTF-8 com BOM, vírgula, ponto decimal e ausências vazias; Parquet preserva tipos. Nomes de colunas únicos em snake_case, texto NFC e espaços normalizados. Códigos não são números de medida. Nove arquivos brutos têm SHA-256 verificado; versões e produtos constam no relatório de execução."),
            ("p", "Os estudos continuam separados. RAIS, PNAD, INEP, Brasscom, Exame e similares são referências da matriz, não bases importadas. A fase 02 não acrescenta dados simulados nem preenche pesquisas ainda não realizadas."),
        ]),
        ("Emprego formal: Novo CAGED", "Filtros, categorias e transformações para P1-P4", [
            ("table", [["Variáveis", "Decisão aplicada", "Justificativa"],
                ["CBO e área de TI", "Famílias 1236/1425/2122/2123/2124/3171/3172; 27 CBOs. Código de seis dígitos, descrição oficial e área analítica.", "Escopo explícito, preservando zeros. Inclui automação; não cobre toda carreira possível de TI."],
                ["Movimento e competência", "saldo 1/-1; calendário derivado; conservar mês do movimento e da declaração.", "Contar eventos, não pessoas ou vagas. MOV sem FOR/EXC não é saldo final ajustado."],
                ["UF e município", "Ligar código CAGED de seis dígitos à chave IBGE única de sete; recortes PE/NE/Brasil.", "Evitar duplicação por join e garantir filtros geográficos legíveis."],
                ["Salário mensal", "Número brasileiro; validade nominal [300,200000]; sinalizar, não remover. Não multiplicar o campo salario por horas/dias.", "A unidade do componente fixo não altera o salário mensal do layout; controles não apagam movimentos."],
                ["Salário real e faixas", "nominal × IPCA(mar/2025)/IPCA(mês). Faixas [0,2000), [2000,4000), [4000,6000), [6000,10000), [10000,15000), [15000,+inf).", "Comparar poder de compra; limites claros, sem converter faixa em ponto exato."],
                ["Idade e jornada", "Idade válida [14,90]; jornada [1,48]. Originais mantidos, sinalizados excluídos apenas de relações/escalas que os usam.", "Limites operacionais de plausibilidade, não conclusão legal; idade não é experiência."],
                ["Escolaridade e vínculo", "Preservar código e texto oficiais; agrupar escolaridade; booleanos anuláveis para indicadores.", "Categorias não viram ordem numérica arbitrária; primeiro emprego não equivale a júnior."]]),
            ("p", "Leitura em lotes de 200.000 linhas limita memória. Foram examinadas 13.530.056 linhas brutas. Nenhuma movimentação selecionada é removida por salário sinalizado. As 1.386 linhas iguais sem ID ficam: a fonte não identifica pessoas e podem ser eventos distintos."),
        ]),
        ("Perfis: State of Data", "Preparação conservadora para P5-P8", [
            ("table", [["Variáveis", "Decisão aplicada", "Justificativa"],
                ["Registro e schema", "5.217 respostas originais; remover só duas linhas completamente iguais; IDs preservam linha de origem.", "Deduplicação explícita, sem apagar respostas apenas parecidas; ID não liga pessoas a outras fontes."],
                ["Gestão, cargo e área", "Indicador de gestor como booleano anulável. Gestor declarado sem cargo técnico recebe Gestao.", "Correção do erro texto/booleano: 1.045 gestores não devem cair em outra área por falha de tipo."],
                ["Senioridade e experiência", "Nível apenas declarado. Até dois anos usa experiência em dados; experiência anterior em TI fica separada.", "Sem inventar júnior e sem confundir entrada em dados com início de toda a carreira."],
                ["Faixa de salário", "Guardar texto, limites e exclusividade; faixa acima de R$40.001 permanece aberta.", "Não criar salário exato, média por ponto médio ou comparação direta com remuneração administrativa."],
                ["Formação, vínculo e trabalho", "Categorias por mapeamento explícito, conservando declarações originais na base completa.", "Reduzir complexidade visual sem esconder distinções; não informado não é uma categoria de emprego."],
                ["Tecnologias e residência", "Tecnologias anuláveis; tabela longa só com seleções. Brasil pelo item de residência; regiões por UF.", "Nulo não é False. Denominador vem de elegibilidade do item; recortes são subconjuntos."],
                ["Busca ativa e proxies", "Manter quatro respostas originais e alvo planejado separado; excluir resposta-alvo e proxies próximos no modelo.", "Ausente não vira classe negativa; intenção não mede saída futura."]]),
            ("p", "Os 403 campos originais geram 405 colunas com ID/fonte; a versão de carreiras tem 51. Nulos podem decorrer de ramificações, como perguntas não feitas a gestores ou desempregados. Não aplicar complete-case global: avaliar elegibilidade por pergunta e evitar excluir sistematicamente perfis."),
        ]),
        ("Pesquisa própria e matriz", "Tratamento de Q01-Q12 e referências para P9-P12", [
            ("table", [["Item", "Tratamento aplicado", "Justificativa e limite"],
                ["Schema e coleta", "35 respostas; reconhecer número da pergunta, inclusive Q02 no fim. Descartar coluna vazia. Guardar mês, não horário exato, no analítico.", "Ordem da exportação não altera semântica. IDs de linha não garantem anonimização."],
                ["Q05: nota 1-5", "Validar domínio ordinal e preservar notas; não deduzir âncoras/direção.", "XLSX não informa o sentido dos extremos; confirmar formulário antes de medir satisfação."],
                ["Q07: Sim/Não", "Três respostas fora do domínio: original preservado, booleano ausente e flag. Denominador válido = 32.", "Não adivinhar intenção nem deslocar respostas para outra pergunta."],
                ["Q08: prioridades", "Reconhecer sete textos completos; de uma a três seleções. 101 linhas derivadas, não 101 pessoas.", "Vírgulas internas não separam opções. Percentual usa participantes que responderam, não total de seleções."],
                ["Q09: expectativa", "Inteiro mensal; revisão fora de [300,200000] ou não parseável. R$5 mantido e sinalizado.", "Não corrigir para milhares nem confundir expectativa com salário recebido; analisar sensibilidade."],
                ["Q12: experiência", "Anos/meses inequívocos convertidos. Intervalo 7-8 mantém limites e exato ausente; zero válido.", "Não transformar intervalo em média ou inventar experiência."],
                ["Q10/Q11 e matriz", "Sim/Não por item; matriz mantém 21 achados e 10 links, com CSD declarado e alertas.", "Emprego/área/regime não equivale ao alvo State of Data. Referência importada não é evidência verificada."]]),
            ("p", "Curso, momento e período permanecem declarados; desperiodizado não vira período zero. O grupo tem tabelas separadas de respostas (35), respostas longas (420) e prioridades (101). Sem cargo padronizado/UF e com coleta em 2026, não medir diferença salarial individual contra o CAGED de 2025."),
        ]),
        ("Nulos, escalas e uso analítico", "Elegibilidade e proteção contra vazamento", [
            ("table", [["Uso", "Regra", "Justificativa"],
                ["Descrição", "Sem imputar média/zero/Não; informar total, válidos, ausentes e exclusões por variável.", "Ausência, não aplicável e zero são diferentes; denominador não pode mudar silenciosamente."],
                ["Salários CAGED", "Usar salario_valido; conservar todos os movimentos nos volumes. Quantis por grupo só com n>=30.", "Evitar estatística salarial instável sem apagar contratações; n>=30 não comprova representatividade."],
                ["Z-score e min-max", "Ajustes do pacote em valores válidos: (x-média)/desvio populacional e (x-min)/(max-min). log1p no salário real.", "Escalas exploratórias são separadas dos reais; inválidos permanecem ausentes na tabela de features."],
                ["Regressão prevista", "Jan/fev treino; março teste. Ajustar codificação/escalas/imputação só no treino; excluir salário nominal, faixas/escalas do alvo e IDs.", "Evitar vazamento e medir relação salarial num período reservado, não trajetória da pessoa."],
                ["Classificação prevista", "State of Data Brasil com alvo respondido; split 80/20 estratificado, semente 12. Excluir alvo, cópias e proxies; não adicionar as 35 respostas G12.", "Perguntas e públicos diferentes não aumentam artificialmente o treino; modelo ainda não executado."],
                ["Publicação G12", "Originais e respostas individuais fora do Git. Revisar consentimento e agregados, células raras e supressão complementar.", "Pseudônimo não elimina reidentificação; agregação pequena exige revisão antes de divulgação."]]),
            ("h", "Pendências de confirmação"),
            ("p", "Permanecem para confirmação: âncoras Q05, três respostas Q07 fora do domínio, expectativa sinalizada, protocolo de recrutamento e autorização de divulgação. A preparação os registra e permite análises restritas; não os resolve por inferência automática."),
        ]),
        ("Pipeline reproduzível", "Da fonte verificada ao pacote validado", [
            ("table", [["Passo", "Execução e saída"],
                ["1. Procedência", "Verificar nove SHA-256 antes de transformar; origem pública e XLSX próprios têm manifestos separados."],
                ["2. Fontes públicas", "prepare_datasets.py: schema, survey, CAGED em lotes, dimensões, recortes, agregados e escalas."],
                ["3. Pesquisa própria", "prepare_grupo12.py: respostas, tabela longa, prioridades, matriz, dicionário e alertas."],
                ["4. Validação", "validate_package.py: CSV/Parquet em valores, fontes, contagens, relações, deflação, categorias e domínios."],
                ["5. Testes e evidência", "unittest; execucao_preparacao.json com ambiente, código, fontes, etapas e SHA-256 dos produtos."]]),
            ("h", "Executar na raiz do repositório"),
            ("code", "python -m pip install -r `\n  inteligencia_de_carreiras/02_preparacao_dados/requirements_reproducao.txt"),
            ("p", "Executar o pipeline completo com os originais locais:"),
            ("code", "python inteligencia_de_carreiras/datasets/scripts/run_preparation.py"),
            ("p", "Para conferir somente o pacote existente, acrescentar --mode validate. O pipeline não baixa dados automaticamente. Em outra máquina, reconstruir o pacote público com download_sources.py e obter os XLSX do grupo por canal autorizado; conferir/registrar os manifestos antes de processar."),
            ("h", "Cache e recursos"),
            ("p", "Cache temporário fora do OneDrive por padrão; --temporary permite escolher outra pasta. Chave inclui o código de transformação e SHA-256 do arquivo CAGED, layout, municípios e IPCA. Mudança de fonte ou regra invalida o reaproveitamento. Temporários não são exports finais nem entram na validação de CSV."),
            ("p", "Reservar alguns GB em disco para os textos descompactados; memória é limitada pela leitura em lotes, mas tabelas finais e exports ainda consomem recursos. Sem acesso à internet, os nove brutos já disponíveis permitem reprodução offline. Fontes privadas não são distribuídas pelo Git."),
        ]),
        ("Controles e resultados da preparação", "Evidência de execução, não de análise exploratória", [
            ("table", [["Controle", "Resultado do pacote revisado"],
                ["CAGED: população", "13.530.056 linhas verificadas; " + br(c["registros_ti"]) + " movimentos de TI; PE " + br(c["registros_pe"]) + "; Nordeste " + br(c["registros_nordeste"]) + "."],
                ["CAGED: salário e cobertura", "690 salários sinalizados; 117.874 válidos. Sem CBO/município sem tradução; 395 jornadas sinalizadas."],
                ["CAGED: duplicatas e agregado", "1.386 linhas iguais sem ID preservadas; 1.227 grupos conciliados com volumes/quantis e bloqueio n<30."],
                ["State of Data", "5.217 originais; 5.215 após duas duplicatas exatas; Brasil 5.076. 1.399 senioridades ausentes mantidas."],
                ["Correção de gestão", br(s["gestores_declarados"]) + " gestores declarados; " + br(s["area_gestao"]) + " enquadrados em Gestao quando cargo técnico não respondido. Tipos conciliados com a origem."],
                ["Grupo 12", "35 respostas/12 perguntas; 420 respostas longas; 101 prioridades; três Q07 fora de domínio; uma expectativa e um intervalo sinalizados."],
                ["Matriz de pesquisa", "21 itens e 10 links preservados. Certezas, suposições e dúvidas são declarações, não verificação externa."],
                ["Rastreabilidade por coluna", br(len(matrix)) + " linhas de decisões na matriz de pré-processamento, incluindo os campos da base completa e dimensões."]]),
            ("h", "Ambiente e execução"),
            ("p", "Python " + execution["python"] + "; " + versions + ". A execução registrada tem modo <b>" + execution["modo"] + "</b>, com fontes e produtos conferidos. O relatório JSON preserva tempos, versões e hashes sem conteúdo das respostas individuais."),
            ("p", "A validação técnica passou com alertas semânticos documentados. Validar estrutura não comprova representatividade, veracidade de relatos ou consentimento. Exploração dos dados e avaliação de regressão/classificação serão executadas nas fases seguintes."),
        ]),
        ("Critérios de aceite e referências", "Rastreabilidade da entrega CC02", [
            ("table", [["Critério solicitado", "Evidência entregue"],
                ["Fontes abertas/próprias e formatos", "Escopo, formatos e unidades no plano; catálogo, registro e dois manifestos. Sem dados simulados."],
                ["Limpeza e normalização", "Nomes/tipos/texto, tradução de códigos, domínio, duplicatas, nulos e limites documentados e implementados."],
                ["Transformações para análise", "Recortes, deflação, faixas, categorias, tabelas longas, agregados e escalas com uso específico."],
                ["Justificativa por variável", "Matriz CSV com dataset, coluna, tipo, nulos, regra, justificativa e relação com P1-P12."],
                ["Reprodução e revisão", "Comando único, ambiente registrado, fontes por SHA-256, validação em valores e testes executados."]]),
            ("h", "Referências"),
            ("p", "Critérios fornecidos pelo grupo: Entregáveis 5ºP - Projeto 2026.1-2, coluna CC Análise e Visualização de Dados. O plano da fase 01 define as perguntas; esta fase justifica como preparar suas variáveis."),
            ("p", '<link href="https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged">MTE: microdados Novo CAGED e layout</link>. <link href="https://www.kaggle.com/datasets/datahackers/state-of-data-brazil-20242025">Data Hackers: State of Data Brazil 2024-2025</link>. IBGE: IPCA SIDRA tabela 1737/variável 2266 e API de Localidades. URLs, datas e hashes no manifesto público.'),
            ("p", "Pesquisa e matriz G12: XLSX fornecidos pelo grupo, copiados intactos e registrados em manifesto próprio. Enunciados, hyperlinks e textos originais foram preservados."),
            ("h", "Situação da etapa"),
            ("p", "A etapa 02 está concluída documental e tecnicamente para este pacote, com alertas explícitos. Aprovação acadêmica depende da avaliação da professora. A etapa 03 começará a exploração P1-P12; revisões por confirmação de respostas devem gerar nova versão de fonte/manifesto, não sobrescrever silenciosamente o histórico."),
        ]),
    ]


def render(content, repo):
    spec = importlib.util.spec_from_file_location("radar_theme", repo / "app/theme.py")
    theme = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(theme)
    ink, muted = colors.HexColor(theme.TEXTO), colors.HexColor(theme.TEXTO_SECUNDARIO)
    font, bold = "Helvetica", "Helvetica-Bold"
    if Path("C:/Windows/Fonts/arial.ttf").exists():
        pdfmetrics.registerFont(TTFont("PrepArial", "C:/Windows/Fonts/arial.ttf"))
        pdfmetrics.registerFont(TTFont("PrepArialBold", "C:/Windows/Fonts/arialbd.ttf"))
        pdfmetrics.registerFontFamily("PrepArial", normal="PrepArial", bold="PrepArialBold")
        font, bold = "PrepArial", "PrepArialBold"
    styles = {
        "title": ParagraphStyle("PrepTitle", fontName=bold, fontSize=22, leading=26, textColor=ink, spaceAfter=5),
        "sub": ParagraphStyle("PrepSub", fontName=font, fontSize=10, leading=14, textColor=muted, spaceAfter=15),
        "h": ParagraphStyle("PrepH", fontName=bold, fontSize=11.3, leading=15, textColor=ink, spaceBefore=10, spaceAfter=5, keepWithNext=True),
        "p": ParagraphStyle("PrepP", fontName=font, fontSize=10.1, leading=14, textColor=ink, spaceAfter=6),
        "code": ParagraphStyle("PrepCode", fontName="Courier", fontSize=8.7, leading=12, textColor=ink, spaceBefore=5, spaceAfter=6),
        "cell": ParagraphStyle("PrepCell", fontName=font, fontSize=9.2, leading=12.4, textColor=ink),
        "head": ParagraphStyle("PrepHead", fontName=bold, fontSize=9.2, leading=12.4, textColor=colors.white),
    }
    width, flow = A4[0] - 84, []
    for page, (title, subtitle, blocks) in enumerate(content):
        if page:
            flow.append(PageBreak())
        flow += [Paragraph(title, styles["title"]), Paragraph(subtitle, styles["sub"])]
        for kind, value in blocks:
            if kind != "table":
                text = escape(value).replace("\n", "<br/>") if kind == "code" else value
                flow.append(Paragraph(text, styles[kind]))
                continue
            widths = [width * .29, width * .71] if len(value[0]) == 2 else [width * .24, width * .39, width * .37]
            cells = [[Paragraph(str(x), styles["head"] if i == 0 else styles["cell"]) for x in row] for i, row in enumerate(value)]
            table = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(theme.GRAFITE)),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(theme.CINZA_CLARO)]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, -1), .4, colors.HexColor(theme.BORDA_CLARA)),
            ]))
            flow += [table, Spacer(1, 8)]
    def footer(canvas, document):
        canvas.setFont(font, 8)
        canvas.setFillColor(muted)
        canvas.drawString(42, 25, "Radar de Carreira em TI - Preparação dos dados")
        canvas.drawRightString(A4[0] - 42, 25, f"{document.page} / {len(content)}")
    doc = SimpleDocTemplate(str(OUT / "plano_de_preparacao.pdf"), pagesize=A4,
                            leftMargin=42, rightMargin=42, topMargin=36, bottomMargin=45,
                            title="Plano de preparação dos dados", author="Grupo 12")
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    reader = PdfReader(OUT / "plano_de_preparacao.pdf")
    if len(reader.pages) != len(content):
        raise ValueError(f"Layout overflow: {len(reader.pages)} pages; expected {len(content)}")
    text = " ".join(page.extract_text() for page in reader.pages)
    for term in ("SHA-256", "CBO", "IPCA", "Q07", "P1-P12", "CC02", "Gestao"):
        assert term in text, term


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads((DATA / "qualidade/relatorio_qualidade.json").read_text(encoding="utf-8"))
    own = json.loads((DATA / "fontes_pesquisa_grupo12.json").read_text(encoding="utf-8"))
    execution = json.loads((DATA / "qualidade/execucao_preparacao.json").read_text(encoding="utf-8"))
    if execution["modo"] != "full":
        raise ValueError("Run the full preparation before generating its completion evidence.")
    rows = column_matrix()
    content = document_content(report, own, execution, rows)
    md = ["# Plano de preparação dos dados", "", "Etapa 02. Versão 1.0. 14 de outubro de 2026.", ""]
    for i, (title, subtitle, blocks) in enumerate(content, 1):
        md += [f"## {i}. {title}", "", subtitle, ""]
        for kind, value in blocks:
            if kind == "table":
                md += ["| " + " | ".join(value[0]) + " |", "| " + " | ".join("---" for _ in value[0]) + " |"]
                md += ["| " + " | ".join(str(x) for x in row) + " |" for row in value[1:]]
            elif kind == "h":
                md += ["### " + value]
            elif kind == "code":
                md += ["```powershell", value.replace(" -r\n", " -r "), "```"]
            else:
                text = re.sub(r'<link href="([^"]+)">(.*?)</link>', r'[\2](\1)', value)
                md += [text.replace("<b>", "**").replace("</b>", "**").replace("<br/>", "\n")]
            md.append("")
    (OUT / "plano_de_preparacao.md").write_text("\n".join(md), encoding="utf-8")
    names = ["pandas", "numpy", "pyarrow", "py7zr", "openpyxl", "reportlab", "pypdf"]
    (OUT / "requirements_reproducao.txt").write_text("\n".join(f"{name}=={importlib.metadata.version(name)}" for name in names) + "\n", encoding="ascii")
    render(content, args.repo)
    print(f"Preparation plan exported: {len(content)} pages; {len(rows)} column decisions.")


if __name__ == "__main__":
    main()
