# Documentação do Radar de Carreiras

Índice geral do repositório. A documentação de inteligência de carreiras descreve
as oito etapas de AVD; os documentos originais deste diretório registram o Ciclo 1
e foram preservados, sem alterações na aplicação existente.

## Por Onde Começar

| Objetivo | Documento |
| --- | --- |
| Entender as áreas e executar o dashboard AVD | [README principal](../README.md) |
| Navegar pelas oito etapas | [Índice de inteligência de carreiras](../inteligencia_de_carreiras/README.md) |
| Ler a síntese técnica completa | [Documentação final em PDF](../inteligencia_de_carreiras/08_documentacao_final/documentacao_final.pdf) ou [Markdown](../inteligencia_de_carreiras/08_documentacao_final/documentacao_final.md) |
| Conferir os dez entregáveis de CC | [Matriz de critérios](../inteligencia_de_carreiras/00_referencias/matriz_criterios.csv) e [guia de entrega](../inteligencia_de_carreiras/08_documentacao_final/guia_entrega.md) |
| Conhecer as fontes e variáveis | [Guia dos datasets](../inteligencia_de_carreiras/datasets/LEIA-ME.md) e [catálogo](../inteligencia_de_carreiras/datasets/catalogo.md) |
| Entender separação das bases e privacidade | [Organização e integração dos dados](../inteligencia_de_carreiras/datasets/organizacao_e_integracao.md) |

## Documentação das Oito Etapas

| Etapa | Leitura principal | Reprodução e evidências |
| --- | --- | --- |
| 01. Plano de análise | [Perguntas, métricas e gráficos](../inteligencia_de_carreiras/01_plano_de_analise/plano_de_analise.md) | [Conferência do plano](../inteligencia_de_carreiras/01_plano_de_analise/verificacao_fase01.md) |
| 02. Preparação | [Plano e justificativas](../inteligencia_de_carreiras/02_preparacao_dados/plano_de_preparacao.md) | [Pipeline e validação](../inteligencia_de_carreiras/02_preparacao_dados/README.md) |
| 03. Análise exploratória | [Síntese dos achados públicos](../inteligencia_de_carreiras/03_analise_exploratoria/sintese_achados.md) | [Notebook, gráficos e reprodução](../inteligencia_de_carreiras/03_analise_exploratoria/README.md) |
| 04. Regressão | [Metodologia e limites](../inteligencia_de_carreiras/04_regressao/metodologia.md) | [Resultados e reprodução](../inteligencia_de_carreiras/04_regressao/README.md) |
| 05. Classificação | [Metodologia e limites](../inteligencia_de_carreiras/05_classificacao/metodologia.md) | [Resultados e reprodução](../inteligencia_de_carreiras/05_classificacao/README.md) |
| 06. Dashboard e publicação | [Proposta de integração web](../inteligencia_de_carreiras/06_dashboard_e_publicacao/proposta_integracao_web.md) | [Executar e testar o aplicativo AVD](../inteligencia_de_carreiras/06_dashboard_e_publicacao/README.md) |
| 07. Consolidação e validação | [Relatório de validação técnica](../inteligencia_de_carreiras/07_consolidacao_e_validacao/relatorio_validacao.md) | [Registro de execução](../inteligencia_de_carreiras/07_consolidacao_e_validacao/registro_execucao.json) e [roteiro de revisão do grupo](../inteligencia_de_carreiras/07_consolidacao_e_validacao/roteiro_revisao.md) |
| 08. Documentação final | [Síntese em PDF](../inteligencia_de_carreiras/08_documentacao_final/documentacao_final.pdf) | [Manifesto e validação documental](../inteligencia_de_carreiras/08_documentacao_final/README.md) |

O pacote atual reúne CAGED de janeiro a março de 2025, State of Data Brazil
2024-2025 e pesquisa própria de 2026. A matriz G12 é uma referência documental,
não um conjunto de respostas individuais. As bases não foram unidas como se
representassem as mesmas pessoas. Originais, microdados tratados e saídas
restritas permanecem locais; o dashboard AVD usa agregados públicos versionados.

## Estado da Entrega

A entrega inicial das oito etapas está versionada no commit `c789019`. O dashboard
AVD está consolidado na versão 1.1 e foi validado tecnicamente de forma local.
O registro da etapa 07 documenta 111 testes, 22 verificações de navegador e 65.761
comparações numéricas sem divergências.

Permanecem pendentes a revisão estruturada pelos colegas/usuários, a incorporação
do feedback real e a hospedagem externa com teste remoto. Há uma proposta de
publicação, não uma URL pública já validada. Esta situação não equivale a
aprovação acadêmica ou validação de uso com participantes.

Relatórios de execução, manifestos, capturas e PDFs são registros do momento da
geração. Por isso podem mencionar commit/push como pendentes antes de `c789019`.
Foram preservados para manter sua rastreabilidade; este índice e o README
principal registram a atualização posterior ao versionamento.

## Documentos Originais do Ciclo 1

Os arquivos abaixo não foram reescritos. Referem-se ao recorte e à implementação
originais, inclusive ao CAGED de janeiro de 2025. Não substituem os planos, o
catálogo e a avaliação das oito etapas atuais de AVD.

| Documento preservado | Escopo original |
| --- | --- |
| [Verificação do layout](00_verificacao_layout.md) | Limites do CAGED e ajuste da promessa inicial |
| [Plano de análise](01_plano_de_analise.md) | Perguntas e visualizações do Ciclo 1 |
| [Plano de preparação](02_plano_de_preparacao.md) | Preparação do pipeline original |
| [Dicionário de variáveis](dicionario_de_variaveis.md) | Variáveis da aplicação existente |
| [Log do ciclo](00_log_do_ciclo.md) | Histórico da implementação original |
| [Identidade visual](identidade_visual.md) | Referência visual existente, reutilizada pelo dashboard AVD |

A aplicação original continua em [app/dashboard.py](../app/dashboard.py), com
pipeline em `src/`, notebook em `notebooks/01_eda.ipynb` e dependências da raiz.
O aplicativo AVD tem [entrada própria](../inteligencia_de_carreiras/06_dashboard_e_publicacao/dashboard.py)
e dependências isoladas. Nenhuma migração ou substituição da parte web existente
foi realizada para documentar a área de dados.
