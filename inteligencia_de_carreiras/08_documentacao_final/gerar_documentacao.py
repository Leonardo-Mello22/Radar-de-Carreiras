"""Build the final PDF and Markdown from shared content and verified public evidence."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent
AREA = OUT.parent
PUBLIC = AREA / "06_dashboard_e_publicacao/dados_publicos"
DATE = "19/10/2026"
VERSION = "1.1"
REPO = "https://github.com/Leonardo-Mello22/Radar-de-Carreiras"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def number(value, digits=0):
    return f"{value:,.{digits}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def percent(value):
    return number(100 * value, 1) + "%"


def collect():
    release = read_json(AREA / "07_consolidacao_e_validacao/registro_execucao.json")
    if release["status"] != "VALIDADO_TECNICAMENTE_AGUARDANDO_REVISAO_DO_GRUPO":
        raise ValueError("A etapa 07 precisa estar validada tecnicamente")
    for name, expected in {**release["codigo_sha256"], **release["evidencias_sha256"]}.items():
        if sha(AREA / name) != expected:
            raise ValueError("Evidencia da etapa 07 desatualizada: " + name)
    meta = read_json(PUBLIC / "manifesto.json")
    for name, expected in meta["arquivos"].items():
        if sha(PUBLIC / name) != expected["sha256"]:
            raise ValueError("Pacote publico alterado: " + name)
    regression = pd.read_csv(PUBLIC / "R1_teste_marco.csv").set_index("modelo")
    classification = pd.read_csv(PUBLIC / "C1_metricas_teste.csv").set_index("modelo")
    employment = pd.read_parquet(PUBLIC / "emprego.parquet")
    profiles = pd.read_parquet(PUBLIC / "perfis.parquet")
    br = employment.query("geo == 'BR' and periodo == '2025T1' and tipo == 'total'").iloc[0]
    pe = employment.query("geo == 'UF_PE' and periodo == '2025T1' and tipo == 'total'").iloc[0]
    sod = profiles.query("geo == 'BR' and senioridade == 'Todos' and modelo == 'Todos'").iloc[0]
    return release, meta, regression, classification, br, pe, sod


def chapters(evidence):
    release, meta, regression, classification, br, pe, sod = evidence
    selected = regression.loc[meta["modelos"]["regressao"]["modelo_selecionado"]]
    logistic = classification.loc[meta["modelos"]["classificacao"]["modelo_selecionado"]]
    baseline = classification.loc["majoritaria"]
    audit = release["auditoria"]
    checks = release["checks_browser_inicial"] + release["checks_browser_ampliado"]
    images = "../07_consolidacao_e_validacao/evidencias/"
    return [
        ("Visão Executiva", [
            ("p", f"Radar de carreiras | Documentação final da solução analítica e visual | Grupo 12, Projeto 5, CESAR School | Versão {VERSION} | {DATE}."),
            ("p", "O Radar comunica informações sobre emprego formal em ocupações de TI e perfis de carreira em dados, com foco inicial em Pernambuco e Nordeste. A solução combina preparação reproduzível, análise exploratória, modelos simples e um dashboard em Streamlit. As fontes são apresentadas lado a lado, sem inventar uma população única ou acompanhar pessoas entre bases."),
            ("table", ["Evidência técnica", "Resultado registrado"], [
                ["Testes da aplicação e dos dados", f"{release['total_testes']} aprovados na etapa 07"],
                ["Verificações no navegador", f"{checks} aprovadas em Chromium"],
                ["Conferência de agregados", f"{number(audit['total_comparacoes'])} comparações; {audit['n_divergencias']} divergências"],
                ["Recortes conferidos", f"{number(audit['recortes_caged'])} CAGED + {number(audit['recortes_state_of_data'])} State of Data"],
            ]),
            ("p", "Estado da entrega: implementação e documentação técnica organizadas nas oito etapas. O dashboard v1.1 funciona localmente e possui evidências funcionais. A documentação final atende ao escopo de CC10: histórico, decisões, capturas e síntese dos insights. Aprovação acadêmica continua sendo atribuição da professora."),
            ("table", ["Etapa", "Resultado"], [
                ["01 - Plano", "Perguntas P1-P12, métricas e justificativas visuais"],
                ["02 - Preparação", "Pipeline, regras de limpeza, categorias e rastreabilidade"],
                ["03 - Exploração", "Distribuições, associações e agrupamentos interpretados"],
                ["04 - Regressão", "Comparação temporal, tendências e resíduos"],
                ["05 - Classificação", "Métricas, matriz de confusão, ROC e precision-recall"],
                ["06 - Dashboard", "Quatro visões e proposta de integração/publicação"],
                ["07 - Consolidação", "Correções, auditoria integral e avaliação funcional local"],
                ["08 - Documentação", "Este relatório, índice das entregas e guia de revisão"],
            ]),
            ("p", "Pendências externas: revisão estruturada pelos colegas, autorização e execução de commit/push, configuração da hospedagem e teste remoto. Não houve teste formal com participantes nem publicação externa. A impressão positiva informal do solicitante não é tratada como validação de usabilidade."),
        ]),
        ("Dados e Preparação", [
            ("table", ["Fonte e unidade", "Volume e período", "Uso e restrição"], [
                ["Novo CAGED MOV: movimentação formal", f"{number(meta['fontes']['caged_ti']['n'])} eventos; jan-mar/2025", "Salários e fluxos das ocupações selecionadas; pacote público agregado"],
                ["State of Data: resposta autodeclarada", f"{number(meta['fontes']['state_of_data_brasil']['n'])} residentes no Brasil; 2024-2025", "Perfis e busca ativa; amostra voluntária, específica de dados"],
                ["Pesquisa G12: resposta ao questionário", "35 participantes, 12 perguntas; coleta em 2026", "Necessidades e intenções; respostas e saídas individuais restritas ao ambiente local"],
                ["Matriz G12: referência ou hipótese", "21 registros documentais, 10 links", "Rastreabilidade da pesquisa; não são participantes nem fatos externamente confirmados"],
            ]),
            ("p", "O recorte CAGED inclui 27 ocupações de sete famílias CBO e dez áreas analíticas. Foram examinadas 13.530.056 linhas brutas para selecionar os 118.564 eventos de TI. As famílias incluem algumas ocupações de automação e não representam todo o setor de tecnologia. PE e Nordeste são subconjuntos do Brasil, não bases adicionais para somar."),
            ("list", [
                "Preservar códigos como texto e tipos anuláveis; priorizar Parquet. CSV de exportação usa UTF-8 com BOM, vírgula e ponto decimal.",
                "Usar salário mensal real, corrigido pelo IPCA para março/2025. Não multiplicar remuneração já mensal por horas ou dias.",
                "Manter os 690 salários CAGED sinalizados nas contagens de movimentos, excluindo-os apenas das estatísticas salariais. Entre admissões, 185 ficam fora da análise de salário.",
                "Preservar eventos CAGED aparentemente iguais: sem identificador de pessoa ou vínculo não há base para remover essas linhas como duplicatas individuais.",
                "No State of Data, não transformar ausência em Não ou senioridade ausente em Júnior. Remover somente duas duplicatas integrais identificadas na preparação.",
                "Calcular quantis diretamente nos eventos elegíveis de cada recorte. Exibir estatísticas salariais e comparações somente com base válida de ao menos 30.",
                "Não converter faixas salariais autodeclaradas em salários exatos; manter a faixa superior aberta. Tecnologias usam denominadores próprios de resposta ao item.",
                "Manter alertas do G12 sem inventar correções: três respostas fora do domínio em Q07, uma expectativa sinalizada, intervalo de experiência e âncoras de escala a confirmar.",
            ]),
            ("links", [("Catálogo, unidades e volumes", "../datasets/catalogo.md"), ("Plano e justificativas de preparação", "../02_preparacao_dados/plano_de_preparacao.md"), ("Registro de fontes e referências ainda não importadas", "../datasets/registro_fontes.csv")]),
        ]),
        ("Decisões e Histórico", [
            ("p", "Fluxo implementado: fontes originais locais, preparação validada, tabelas tratadas por fonte, exploração, modelagem separada, agregados públicos e dashboard. Manifestos e SHA-256 identificam código, insumos e produtos. Os notebooks e relatórios preservam o contexto da etapa em que foram executados; o estado consolidado atual está nesta documentação e na matriz de critérios."),
            ("table", ["Momento", "Decisão e justificativa"], [
                ["Plano e integração", "Manter CAGED, State of Data e G12 separados. Unidades, períodos e populações são incompatíveis com uma concatenação de pessoas."],
                ["Preparação", "Separar contagem de eventos de validade salarial, preservar ausências e documentar categorias derivadas. Não fabricar respostas nem reconstruir informações ausentes."],
                ["Exploração", "Usar posição, comprimento e eixos comparáveis para contagens e quantis. Agrupamentos são descritivos, não classes naturais de profissionais."],
                ["Modelagem", "Aprender pré-processamento apenas no treino. Selecionar antes do teste e comparar com referência simples; manter erros e resultados limitados visíveis."],
                ["Dashboard inicial", "Criar entrypoint próprio na área de inteligência de carreiras e reutilizar a identidade visual, preservando app/, src/, docs/ e notebooks/ históricos."],
                ["Consolidação v1.1", "Persistir filtros, explicitar o recorte, corrigir o gráfico por ocupação e restaurar padrões explicitamente. Comparar o CSV realmente baixado com o recorte."],
                ["Documentação final", "Reutilizar evidências verificadas, sem retreinar modelos nem alterar números. Distinguir entrega técnica, feedback de pessoas e hospedagem."],
            ]),
            ("list", [
                "Hierarquia: marca discreta, navegação previsível, filtros recolhíveis, indicadores e depois gráficos. Quatro visões: Emprego formal, Perfis em dados, Modelos e Fontes.",
                "Cores: laranja para destaque, neutros para comparação e alertas textuais. Barras começam em zero; percentis aparecem como faixa e mediana.",
                "Contexto persistente: fonte, período, geografia, ocupação e bases válidas acompanham o resultado. Recortes vazios ou insuficientes têm mensagens próprias.",
                "Interatividade: filtros por fonte são independentes; filtros exploratórios não alteram treino/teste ou métricas congeladas dos modelos.",
            ]),
            ("links", [("Proposta visual e de publicação", "../06_dashboard_e_publicacao/proposta_integracao_web.md"), ("Histórico de ajustes e feedback real", "../07_consolidacao_e_validacao/feedback_e_ajustes.csv")]),
        ]),
        ("Síntese dos Insights", [
            ("table", ["Achado observado", "Interpretação e limite"], [
                [f"Mediana de admissão: PE R$ {number(pe.admissoes_p50)}; Brasil R$ {number(br.admissoes_p50)}.", "Salário mensal a preços de março/2025. Diferenças refletem também composição de cargos; não são salário Júnior ou efeito causal regional."],
                [f"Brasil: {number(br.admissoes)} admissões e {number(br.desligamentos)} desligamentos; diferença MOV {number(br.diferenca_mov)}. PE: diferença {number(pe.diferenca_mov)}.", "Contagens incluem salários sinalizados. Sem FOR/EXC, não apresentar a diferença MOV como saldo oficial ajustado."],
                ["Idade e salário: Spearman 0,510 em 60.862 pares; jornada e salário: -0,054.", "Associação descritiva. Idade não equivale a experiência e não mede crescimento individual ou retorno da formação."],
                ["67 perfis UF/área agrupados; k=5 teve silhouette 0,410 entre k=2 e 5.", "Perfis cobrem 94,8% das admissões salariais válidas, com peso igual por perfil. Não provar cinco grupos naturais ou ranquear pessoas/regiões."],
                [f"{number(sod.n_salarios)} respostas salariais válidas em {number(sod.n_respostas)} residentes no Brasil; faixa modal de R$ 8.001 a R$ 12.000/mês.", "Resultado da pesquisa voluntária de dados, não de todo TI. Faixa não vira remuneração exata ou média calculada por ponto médio."],
                ["SQL: 87,7% das 3.502 respostas válidas ao item (3.070 seleções).", "Tecnologia declarada não mede vagas ou demanda empresarial. Itens têm bases distintas e múltiplas escolhas podem somar mais de 100%."],
                [f"Busca ativa: {number(sod.n_ativos)} de {number(sod.n_alvo)} respostas válidas ({percent(sod.proporcao_ativa)}).", "As 342 ausências não são negativas. Busca contemporânea declarada não é desligamento futuro ou probabilidade individual de saída."],
            ]),
            ("p", "Implicação para a solução: priorizar filtros por geografia e ocupação, distribuições em vez de promessa de salário individual, bases válidas visíveis e explicações sobre o que cada fonte mede. Achados da pesquisa própria G12 permanecem em saídas locais restritas; não são publicados neste relatório ou incorporados como se fossem novos eventos CAGED."),
            ("links", [("Síntese pública da exploração", "../03_analise_exploratoria/sintese_achados.md"), ("Notebook-fonte da exploração", "../03_analise_exploratoria/analise_exploratoria.ipynb")]),
        ]),
        ("Modelagem e Avaliação", [
            ("p", "Regressão: 60.862 admissões salariais válidas do CAGED. Escolha por MAE na validação janeiro para fevereiro; treino final com 41.037 eventos de jan-fev e teste reservado com 19.825 de março. Referência: mediana do treino. O modelo múltiplo usa idade, horas, CBO, UF e escolaridade, com Ridge alpha=10 fixo."),
            ("table", ["Regressor", "MAE (R$)", "RMSE (R$)", "R²"], [
                [label, number(regression.loc[key].mae), number(regression.loc[key].rmse), number(regression.loc[key].r2, 3)]
                for key, label in [("mediana", "Mediana do treino"), ("idade", "Linear: idade"), ("multipla", "Linear: cinco variáveis")]
            ]),
            ("p", f"O modelo escolhido antes do teste reduziu MAE em {number(selected.ganho_mae_vs_mediana_pct, 1)}% frente à referência. Foram mantidas {int(selected.previsoes_negativas)} previsões negativas ({percent(selected.previsoes_negativas/selected.n)} do teste), expondo a limitação linear. Melhorar o erro agregado não valida uma calculadora salarial pessoal ou previsão de carreira."),
            ("p", "Classificação: State of Data, 4.734 alvos válidos; treino/teste estratificados 80/20, semente 12 (3.787/947). Seleção pela Average Precision média em cinco folds somente do treino; logística escolhida, limiar fixo 0,5. Entradas: senioridade, ensino, vínculo agrupado, trabalho e experiência em dados. Pergunta-alvo e variáveis com texto de busca não entram."),
            ("table", ["Classificador", "Acurácia", "Precisão", "Recall", "F1", "AUC", "AP"], [
                [label, percent(classification.loc[key].acuracia), percent(classification.loc[key].precisao), percent(classification.loc[key].recall), number(classification.loc[key].f1, 3), number(classification.loc[key].roc_auc, 3), number(classification.loc[key].average_precision, 3)]
                for key, label in [("majoritaria", "Majoritária"), ("logistica", "Logística"), ("arvore", "Árvore")]
            ]),
            ("p", f"Na logística: {int(logistic.tp)} verdadeiros positivos, {int(logistic.fn)} falsos negativos, {int(logistic.fp)} falsos positivos e {int(logistic.tn)} verdadeiros negativos. O modelo deixa de identificar {percent(logistic.fn/logistic.n_ativos)} dos positivos. A referência majoritária acerta {percent(baseline.acuracia)}, mas tem recall zero. Portanto, acurácia isolada seria enganosa; não usar os modelos para rotular empregados ou orientar contratação/desligamento."),
            ("p", "Nenhum teste foi reutilizado para escolher modelo, hiperparâmetros ou limiar. AP não é área trapezoidal genérica da curva PR. São avaliações observacionais: um mês reservado na regressão e uma mesma coleta na classificação, sem validação temporal externa desta última."),
            ("links", [("Regressão: notebook executado e gráficos", "../04_regressao/resultados/regressao_salarial.html"), ("Classificação: notebook executado e gráficos", "../05_classificacao/resultados/classificacao_busca_ativa.html")]),
        ]),
        ("Evidência: Emprego Formal", [
            ("p", "Captura real da versão 1.1, em desktop 1440x1000. Recorte: SP, fevereiro/2025, CBO 212405 (Analista de Desenvolvimento de Sistemas). O gráfico de faixa salarial acompanha a ocupação, mesmo com Todas as áreas selecionado."),
            ("figure", "Indicadores, faixa p10-p90 com mediana e volumes mensais. Captura do viewport, não de todo o conteúdo rolável.", images + "01_recorte_consolidado_desktop.png", 390),
            ("list", [
                "Os números deste recorte são 3.058 admissões, 2.911 desligamentos e diferença MOV 147; a mediana real de admissão é aproximadamente R$ 7.590.",
                "A identificação do cargo/CBO permanece visível com o painel fechado. P10/p90 não são mínimo/máximo nem remuneração inicial Júnior.",
                "A consolidação corrigiu um aviso falso de base insuficiente no gráfico de ocupação. O download é comparado ao conteúdo agregado efetivamente filtrado.",
                "Filtros ficam na sessão ao trocar de visão. Restaurar filtros usa padrões explícitos e não altera os filtros da outra fonte.",
            ]),
            ("links", [("Captura original em resolução integral", images + "01_recorte_consolidado_desktop.png"), ("Aplicativo implementado", "../06_dashboard_e_publicacao/dashboard.py")]),
        ]),
        ("Evidência: Modelos", [
            ("p", "A captura mostra a referência majoritária, não a logística selecionada no treino. Manter a referência visível permite discutir por que acurácia sem recall não valida detecção de busca ativa."),
            ("figure", "Referência majoritária: 621 negativos corretos, 326 falsos negativos e nenhum positivo identificado. A matriz preserva as contagens; a cor é normalizada por classe observada.", images + "02_modelo_referencia_desktop.png", 390),
            ("list", [
                "O seletor compara resultados já calculados, sem retreinar ou escolher pelo teste. Os filtros exploratórios não redefinem a população de avaliação dos modelos.",
                "A logística é apresentada com recall de 12,9%, e não como solução pronta para decisão individual. Os erros e limites acompanham a comunicação dos resultados.",
                "ROC e precision-recall estão no aplicativo e no notebook executado. A curva PR usa degraus, evitando representar a referência constante como uma diagonal interpolada enganosa.",
            ]),
            ("links", [("Captura original em resolução integral", images + "02_modelo_referencia_desktop.png"), ("Métricas agregadas de classificação", "../05_classificacao/resultados/tabelas/C1_metricas_teste.csv")]),
        ]),
        ("Validação e Telas Menores", [
            ("p", f"Execução técnica da etapa 07: {release['total_testes']} testes aprovados; {checks} verificações no Chromium; {number(audit['total_comparacoes'])} comparações numéricas sem divergências em {number(audit['recortes_caged']+audit['recortes_state_of_data'])} recortes. A etapa 08 confere integridade e documentação, sem declarar novos testes de aplicação ou retreinamento."),
            ("pair", [("Emprego: contexto e indicadores", images + "03_emprego_mobile.png"), ("Perfis após restauração: Brasil", images + "04_perfis_mobile.png")], 355),
            ("p", "Capturas em 360x800. A bateria ampliada verifica as quatro visões em 360x800, 768x1024 e 1440x1000, incluindo gráficos não vazios e ausência de overflow horizontal. A bateria inicial também cobre 390x844. O QA aguarda a execução real do Streamlit e a atualização visual antes de conferir o recorte."),
            ("p", "Composição da execução: preparação 17; exploração 11; regressão 17; classificação 24; dashboard inicial 23; consolidação 19. Os resultados por suite e as versões de ambiente estão nos registros de execução da etapa 06 e da etapa 07."),
            ("p", "Verificações cobrem filtros dependentes, persistência, restauração, sessões separadas, estados vazios/insuficientes, CSV realmente baixado, integridade do pacote e seleção básica por teclado. Isso não é certificação de acessibilidade, teste com leitor de tela ou validação em todos os navegadores."),
            ("links", [("Registro da execução e hashes", "../07_consolidacao_e_validacao/registro_execucao.json"), ("Auditoria numérica integral", "../07_consolidacao_e_validacao/resultados/auditoria_numerica.json")]),
        ]),
        ("Limites e Melhorias", [
            ("list", [
                "Cobertura: CAGED mede emprego formal no recorte de ocupações, não PJ, informalidade ou todo TI. MOV não inclui os ajustes FOR/EXC.",
                "Tempo: salários a preços de março/2025 e pesquisa 2024-2025 não descrevem remuneração atual de 2026. Três meses não demonstram sazonalidade ou tendência anual.",
                "Unidade: eventos não são pessoas ou vínculos acompanhados; não inferir promoção, evolução individual ou causalidade por comparar grupos.",
                "Pesquisa: amostra voluntária e ramificações geram viés de seleção/elegibilidade. Três residentes no Brasil têm UF ausente e não são atribuídos a um estado fictício.",
                "Modelos: previsões negativas e baixo recall permanecem. Não há validação externa, auditoria de equidade ou autorização para uso em decisões laborais individuais.",
                "Privacidade: respostas G12, IDs, previsões e escores individuais não entram no pacote público. A regra de n mínimo não prova anonimização universal ou representatividade.",
                "Referências: RAIS, PNAD, INEP, Base dos Dados, Brasscom e Exame são contexto ou possíveis ampliações, não microdados adicionais já importados neste pacote.",
            ]),
            ("table", ["Prioridade", "Melhoria e critério de conclusão"], [
                ["Antes da revisão final", "Executar o roteiro com colegas; registrar observações reais, decisão, correção e reteste. Ainda não realizado."],
                ["Antes da divulgação", "Revisar arquivos versionáveis e autorização de envio; depois configurar Streamlit e validar a URL remota."],
                ["Próximo ciclo", "Avaliar leitor de tela, contraste sistemático e outros navegadores; não afirmar conformidade sem essas verificações."],
                ["Ampliação de dados", "Adicionar competências/ajustes e novas fontes apenas com cobertura, unidade e procedência documentadas."],
                ["Evolução analítica", "Validar em outro período/coleta e definir custos de erro antes de mudar limiares ou recomendar uso dos modelos."],
            ]),
            ("p", "Histórico de feedback: o solicitante viu a prévia e achou boa; isso é uma impressão informal real. A revisão estruturada pelos amigos ainda será feita. Melhorias de navegação, gráficos, download e restauração vieram da revisão técnica/visual, não de um estudo com usuários inventado."),
            ("links", [("Roteiro para revisão real", "../07_consolidacao_e_validacao/roteiro_revisao.md"), ("Registro de feedback e ajustes", "../07_consolidacao_e_validacao/feedback_e_ajustes.csv")]),
        ]),
        ("Reprodução e Entrega", [
            ("p", "Para abrir o dashboard, basta o repositório com o pacote público agregado; os arquivos brutos, as respostas G12 e os datasets tratados locais não são necessários. Recomendação de ambiente reproduzível: Python 3.12, ambiente virtual e versões fixadas nos requirements."),
            ("code", "# Na raiz do repositorio, com o ambiente Python ativo\ncd inteligencia_de_carreiras/06_dashboard_e_publicacao\npython -m pip install -r requirements.txt\npython -m streamlit run dashboard.py --global.developmentMode false --server.port 8502"),
            ("p", "Usar outra porta se 8502 estiver ocupada. O endereço local 127.0.0.1 só funciona na máquina que executa o servidor. O envio deste endereço aos colegas não publica o aplicativo. A proposta de hospedagem Streamlit está pronta, mas a implantação externa ainda não foi realizada."),
            ("p", "Para reconstruir análises e executar a validação completa, seguir os READMEs das etapas 02-07 com os insumos locais necessários. Não publicar os dados privados para facilitar a reprodução. Para regenerar esta documentação, executar gerar_documentacao.py e validar_documentacao.py nesta pasta; a validação visual do PDF continua sendo uma etapa explícita."),
            ("links", [
                ("Guia de entrega, evidências CC01-CC10 e checklist", "guia_entrega.md"),
                ("Rubrica original da disciplina", "../00_referencias/criterios_avd_cc.pdf"),
                ("Matriz atualizada de critérios", "../00_referencias/matriz_criterios.csv"),
                ("Plano de análise e decisões visuais", "../01_plano_de_analise/plano_de_analise.md"),
                ("Preparação e reprodução dos dados", "../datasets/LEIA-ME.md"),
                ("Manifesto do pacote público", "../06_dashboard_e_publicacao/dados_publicos/manifesto.json"),
                ("Proposta de integração e hospedagem", "../06_dashboard_e_publicacao/proposta_integracao_web.md"),
                ("Repositório de origem", REPO),
                ("MTE: origem dos microdados", "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged"),
                ("State of Data: origem da pesquisa pública", "https://www.kaggle.com/datasets/datahackers/state-of-data-brazil-20242025"),
            ]),
            ("p", "Caminhos de evidência são relativos a esta pasta; o Markdown é o índice navegável no repositório. URLs de origem são referências registradas, não afirmação de checagem online nesta etapa. Este documento não foi submetido à disciplina, enviado aos colegas, publicado, commitado ou enviado ao GitHub automaticamente."),
        ]),
    ]


def markdown(document):
    lines = ["# Radar de Carreiras - Documentação Final", ""]
    links = []
    for index, (title, blocks) in enumerate(document, 1):
        lines += [f"## {index}. {title}", ""]
        for kind, *values in blocks:
            if kind == "p":
                lines += [values[0], ""]
            elif kind == "list":
                lines += ["- " + item for item in values[0]] + [""]
            elif kind == "table":
                head, rows = values
                lines += ["| " + " | ".join(head) + " |", "| " + " | ".join(["---"] * len(head)) + " |"]
                lines += ["| " + " | ".join(map(str, row)) + " |" for row in rows] + [""]
            elif kind == "code":
                lines += ["```powershell", values[0], "```", ""]
            elif kind == "links":
                for label, target in values[0]:
                    lines.append(f"- [{label}]({target})")
                    links.append(target)
                lines.append("")
            elif kind == "figure":
                caption, path, _ = values
                lines += [f"![{caption}]({path})", "", caption, ""]
                links.append(path)
            elif kind == "pair":
                for label, path in values[0]:
                    lines += [f"![{label}]({path})", ""]
                    links.append(path)
            else:
                raise ValueError("Unknown content block: " + kind)
    return "\n".join(lines), sorted(set(links))


def make_pdf(document, path):
    regular, bold = Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("Radar", str(regular)))
        pdfmetrics.registerFont(TTFont("Radar-Bold", str(bold)))
        font, strong = "Radar", "Radar-Bold"
    else:
        font, strong = "Helvetica", "Helvetica-Bold"
    ink, teal, muted = colors.HexColor("#1D2228"), colors.HexColor("#126660"), colors.HexColor("#555E68")
    body = ParagraphStyle("Body", fontName=font, fontSize=9.3, leading=13.1, textColor=ink, spaceAfter=8)
    heading = ParagraphStyle("Heading", parent=body, fontName=strong, fontSize=22, leading=27, spaceAfter=16)
    small = ParagraphStyle("Small", parent=body, fontSize=8.1, leading=11, textColor=muted, spaceAfter=8)
    cell = ParagraphStyle("Cell", parent=body, fontSize=8.2, leading=11, spaceAfter=0)
    head = ParagraphStyle("TableHead", parent=cell, fontName=strong, textColor=teal)
    code = ParagraphStyle("Code", fontName="Courier", fontSize=7.7, leading=12, textColor=ink, backColor=colors.HexColor("#F2F5F6"), borderPadding=8, spaceAfter=12)
    width = A4[0] - 88
    story = []

    def para(text, style=body):
        return Paragraph(escape(str(text)), style)

    def figure(relative, max_height, max_width=width):
        with PILImage.open(OUT / relative) as asset:
            w, h = asset.size
        scale = min(max_width / w, max_height / h)
        return Image(str(OUT / relative), width=w * scale, height=h * scale)

    for index, (title, blocks) in enumerate(document, 1):
        if index > 1:
            story.append(PageBreak())
        story.append(para(f"{index:02d}  {title}", heading))
        for kind, *values in blocks:
            if kind == "p":
                story.append(para(values[0]))
            elif kind == "list":
                for item in values[0]:
                    story.append(para("- " + item))
            elif kind == "table":
                columns, rows = values
                if len(columns) == 2:
                    widths = [width * .31, width * .69]
                elif len(columns) == 3:
                    widths = [width * .26, width * .27, width * .47]
                elif len(columns) == 4:
                    widths = [width * .43, width * .2, width * .21, width * .16]
                else:
                    widths = [width * .23] + [width * .77 / (len(columns) - 1)] * (len(columns) - 1)
                data = [[para(v, head) for v in columns]] + [[para(v, cell) for v in row] for row in rows]
                table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F2F0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FA")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBELOW", (0, 0), (-1, 0), .7, teal),
                ]))
                story += [table, Spacer(1, 11)]
            elif kind == "code":
                story.append(Preformatted(values[0], code))
            elif kind == "links":
                for label, target in values[0]:
                    story.append(Paragraph(f'<link href="{escape(target, quote=True)}" color="#126660">{escape(label)}</link>', small))
            elif kind == "figure":
                caption, relative, height = values
                story += [figure(relative, height), Spacer(1, 8), para(caption, small)]
            elif kind == "pair":
                entries, height = values
                table = Table([[figure(relative, height, width / 2 - 18) for _, relative in entries],
                               [para(label, small) for label, _ in entries]], colWidths=[width / 2] * 2)
                table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
                story += [table, Spacer(1, 6)]

    def frame(canvas, doc):
        canvas.saveState()
        canvas.setFont(strong, 8)
        canvas.setFillColor(ink)
        canvas.drawString(44, A4[1] - 30, "RADAR DE CARREIRAS")
        canvas.setFont(font, 7.5)
        canvas.setFillColor(muted)
        canvas.drawRightString(A4[0] - 44, A4[1] - 30, "DOCUMENTAÇÃO FINAL | V1.1")
        canvas.setStrokeColor(colors.HexColor("#D8DFE3"))
        canvas.line(44, A4[1] - 39, A4[0] - 44, A4[1] - 39)
        canvas.drawString(44, 25, "Grupo 12 | Projeto 5 | CESAR School | " + DATE)
        canvas.drawRightString(A4[0] - 44, 25, str(doc.page))
        canvas.restoreState()

    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=44, rightMargin=44, topMargin=55,
                      bottomMargin=43, title="Radar de Carreiras - Documentação Final", author="Grupo 12 - Projeto 5",
                      subject="CC10: processo analítico, decisões, evidências e insights").build(story, onFirstPage=frame, onLaterPages=frame)


def main():
    evidence = collect()
    document = chapters(evidence)
    text, links = markdown(document)
    (OUT / "documentacao_final.md").write_text(text, encoding="utf-8")
    make_pdf(document, OUT / "documentacao_final.pdf")
    inputs = [AREA / "07_consolidacao_e_validacao/registro_execucao.json", PUBLIC / "manifesto.json",
              AREA / "03_analise_exploratoria/sintese_achados.md", AREA / "04_regressao/sintese_achados.md",
              AREA / "05_classificacao/sintese_achados.md", AREA / "datasets/catalogo.md", AREA / "datasets/registro_fontes.csv",
              AREA / "00_referencias/matriz_criterios.csv", AREA / "00_referencias/criterios_avd_cc.pdf"]
    inputs += [PUBLIC / "R1_teste_marco.csv", PUBLIC / "C1_metricas_teste.csv", PUBLIC / "emprego.parquet", PUBLIC / "perfis.parquet"]
    inputs += sorted((AREA / "07_consolidacao_e_validacao/evidencias").glob("*.png"))
    outputs = [OUT / name for name in ["documentacao_final.md", "documentacao_final.pdf", "README.md", "guia_entrega.md"]]
    report = {"versao": VERSION, "gerado_em": datetime.now(timezone.utc).isoformat(), "referencia_local": DATE,
              "capitulos": [title for title, _ in document], "links": links,
              "fontes_sha256": {str(p.relative_to(AREA)): sha(p) for p in inputs},
              "codigo_sha256": {p.name: sha(p) for p in [Path(__file__), OUT / "validar_documentacao.py", OUT / "requirements.txt"]},
              "produtos_sha256": {p.name: sha(p) for p in outputs},
              "validacao_aplicacao_referenciada": {"total_testes": evidence[0]["total_testes"], "checks_browser": evidence[0]["checks_browser_inicial"] + evidence[0]["checks_browser_ampliado"], "data": evidence[0]["executado_em"]},
              "testes_aplicacao_reexecutados_nesta_etapa": False,
              "pendencias_atuais": ["Revisao estruturada do grupo", "Commit/push quando solicitado", "Hospedagem e teste remoto", "Revisao de autorizacao antes de divulgar G12"],
              "publicacao_externa": False, "commit_push_realizado": False}
    (OUT / "manifesto_documentacao.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "DOCUMENTACAO_GERADA_AGUARDANDO_VALIDACAO", "capitulos": len(document)}), flush=True)


if __name__ == "__main__":
    main()
