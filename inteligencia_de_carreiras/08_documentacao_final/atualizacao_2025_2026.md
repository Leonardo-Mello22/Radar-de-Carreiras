# Radar de Carreiras: entrega ampliada 2025–2026

Esta atualização estende as oito etapas existentes. Os notebooks, registros e
PDFs originais continuam descrevendo o recorte com que foram produzidos. A
aplicação do Ciclo 1 em `app/` não foi alterada.

| Etapa | O que foi atualizado |
| --- | --- |
| 01. Plano | P1–P4 passam a cobrir 21 meses do CAGED; P2 compara os mesmos nove meses de cada ano. P5–P8 comparam edições separadas do State of Data. P9–P12 continuam na pesquisa própria, sem nova coleta. |
| 02. Preparação | [Novo lote](../datasets/ATUALIZACAO_2025_2026.md), com manifesto, recorte ocupacional original, IPCA em março/2025, tratamento de duplicatas e faixas inválidas, e mapa de tecnologias por edição. |
| 03. Exploração | [Notebook executado](../03_analise_exploratoria/analise_ampliada.ipynb) com série, faixas, associações salariais, perfil, tecnologias e busca ativa. A pesquisa CESAR School continua separada. |
| 04. Regressão | Nova avaliação temporal: ajuste interno jan–set/2025, validação out–dez/2025, ajuste final no ano de 2025 e teste jan–set/2026. |
| 05. Classificação | Nova avaliação entre edições: treino e seleção interna em 2024/2025; teste reservado em 2025/2026. |
| 06. Dashboard | [Aplicativo](../06_dashboard_e_publicacao/README.md) com períodos comparáveis, seletor de edição e diagnósticos dos novos modelos. Mantém as cinco abas e o layout existente. |
| 07. Validação | [Testes de dados e interface](../06_dashboard_e_publicacao/tests/test_dashboard.py) e [verificação desktop/mobile](../07_consolidacao_e_validacao/verificar_ampliacao.py). |
| 08. Documentação | Este registro, o guia dos datasets e o [manifesto público](../06_dashboard_e_publicacao/dados_ampliados/manifesto.json) documentam o que mudou e o que permanece histórico. |

## Dados e resultados

- **CAGED:** 842.731 movimentações de TI nos 21 meses. São 483.006 em 2025
  inteiro e 359.725 em jan–set/2026. O comparável de jan–set/2025 é 370.147
  eventos. No Brasil, as admissões do recorte passaram de 192.657 para 182.425
  (−5,3%); em Pernambuco, de 4.141 para 5.016 (+21,1%). São eventos nos arquivos
  MOV, não pessoas únicas, vagas abertas ou o saldo oficial ajustado.
- **State of Data:** 5.215 e 3.494 respostas tratadas nas edições 2024/2025 e
  2025/2026; o painel usa os recortes de residentes no Brasil, respectivamente
  5.076 e 3.372. Entre as respostas válidas à pergunta de busca ativa, as
  proporções nacionais ficaram perto de 34,4% nas duas edições. As amostras
  são voluntárias, não um acompanhamento das mesmas pessoas.
- **CESAR School:** 35 respostas, mostradas de forma agregada na aba própria.
  Nenhuma resposta individual da turma é carregada no painel.
- **Regressão:** 249.346 admissões válidas no treino e 182.057 no teste.
  A regressão múltipla teve MAE de **R$ 2.778**, contra **R$ 3.911** da
  mediana do treino (cerca de 29% menor). R² de 0,438. As 3.263 estimativas
  negativas foram mantidas na avaliação; não é uma calculadora pessoal.
- **Classificação:** 4.734 respostas válidas no treino e 3.123 no teste.
  A logística obteve **66,7% de acurácia**, contra **65,6%** da classe
  majoritária. O recall foi de **7,5%** (81 de 1.074 casos ativos),
  F1 de 0,135, ROC-AUC de 0,579 e AP de 0,436. Não serve para decidir
  quem está procurando emprego individualmente.

## Decisões e reprodução

O CAGED mantém as famílias CBO e a base monetária de março/2025. Comparações
salariais usam pelo menos 30 salários válidos por grupo; percentis anuais são
recalculados nos eventos originais do recorte, nunca pela média de percentis
mensais. Os modelos aprendem apenas no treino. A classificação usa quatro
campos de perfil compatíveis e exclui a situação de emprego bruta, que
contém respostas relacionadas ao alvo. Categorias não vistas no treino
são tratadas pelo codificador; ausência de resposta não vira busca negativa.

O pacote ampliado contém apenas agregados e diagnósticos, com hashes por
arquivo. O aplicativo mantém `dados_publicos/` como pacote histórico, lê
`dados_ampliados/` e usa o JSON agregado da pesquisa CESAR School existente.
Não requer microdados nem bibliotecas de treinamento para rodar.

Para refazer a entrega, prepare as bases conforme o [guia do lote](../datasets/ATUALIZACAO_2025_2026.md),
rode [a geração de análises e agregados](../06_dashboard_e_publicacao/preparar_ampliacao.py),
execute [o notebook](../03_analise_exploratoria/executar_ampliacao.py) e rode os testes
descritos no [guia do dashboard](../06_dashboard_e_publicacao/README.md).
Hospedagem externa e revisão com usuários não foram realizadas nesta atualização.
