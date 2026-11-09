# Plano de análise

**Adendo 2025–2026:** P1–P4 cobrem os 21 meses do Novo CAGED, com P2 comparando
jan–set entre anos; P5–P8 mantêm as duas edições da pesquisa separadas. P9–P12
continuam com a amostra original do Grupo 12. Veja o
[roteiro atualizado](../08_documentacao_final/atualizacao_2025_2026.md).

O plano define escopo, fontes, perguntas, métricas, visualizações, princípios de
comunicação e protocolos previstos para regressão e classificação.

- [PDF para leitura e apresentação](plano_de_analise.pdf).
- [Versão editável e versionável](plano_de_analise.md).
- [Matriz de perguntas e métricas](matriz_perguntas_metricas.csv).
- [Conferência dos cinco critérios da fase 01](verificacao_fase01.md).

Revisão 1.1: 12 perguntas de análise, incluindo quatro específicas da pesquisa
própria. Há dados públicos, 35 respostas do questionário G12 e 21 referências da
matriz. Os datasets são separados; necessidades e intenções não são confundidas
com movimentações de emprego ou remuneração efetiva.

As quantidades descrevem os arquivos. Hipóteses, relações, modelos e validação da
solução continuam para as fases seguintes. A fase 01 está completa em relação ao
conteúdo documental solicitado em CC, não significa aprovação da professora.
Os alertas dos dados e as confirmações necessárias estão na conferência.

Para regenerar o PDF, Markdown e matrizes, após importar a pesquisa própria:

```powershell
python -m pip install -r inteligencia_de_carreiras/01_plano_de_analise/requirements_documentacao.txt
python inteligencia_de_carreiras/01_plano_de_analise/gerar_plano.py --repo .
```
