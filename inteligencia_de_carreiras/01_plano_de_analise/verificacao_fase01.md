# Conferência da fase 01

Revisão 1.1, 14 de outubro de 2026. Escopo: plano de análise da coluna CC,
Análise e Visualização de Dados, no documento de critérios fornecido pelo grupo.

## Resultado

**Completa documentalmente nos cinco componentes solicitados.** O plano revisado
tem 12 perguntas, fontes e universos, métricas, objetivos da comunicação e
justificativas visuais. A conferência é interna: não substitui a avaliação da professora
nem conclui preparação acadêmica, exploração, modelos ou dashboard.

| Componente solicitado | Evidência verificável | Situação |
| --- | --- | --- |
| Dados que serão utilizados | Escopo do plano; catálogo e registro de fontes; arquivos locais e manifestos de procedência. | Atendido |
| Perguntas de análise | P1-P4 CAGED; P5-P8 State of Data; P9-P12 pesquisa própria, com universos e limites. | Atendido |
| Métricas previstas | Quantis, contagens, proporções, associações e métricas de modelos; denominadores e regras de elegibilidade. | Atendido |
| Visualizações e objetivos da comunicação | Tipo de gráfico e objetivo explícito para cada pergunta; duas seções visuais no plano. | Atendido |
| Justificativas por percepção e design | Posição, comprimento, escalas, ordem, distribuição, contraste, hierarquia e privacidade. | Atendido |

Consulte o [plano](plano_de_analise.md), a
[matriz de perguntas e métricas](matriz_perguntas_metricas.csv), o
[catálogo de dados](../datasets/catalogo.md) e os
[critérios originais](../00_referencias/criterios_avd_cc.pdf).

## Ajustes feitos nesta revisão

- Pesquisa própria incorporada como estudo separado: 35 respostas, 12 perguntas e tabelas derivadas.
- Matriz incorporada como desk research: 21 itens e 10 links, sem transformar confiança declarada em evidência checada.
- Objetivos de comunicação passaram a expressar a mensagem de cada gráfico, não apenas repetir métricas.
- Plano ampliado para dificuldades, prioridades, expectativa salarial e intenções da amostra G12.
- Removida a interpretação de progressão individual entre admissões e desligamentos do CAGED; são grupos diferentes.
- Referências sem microdados importados identificadas no registro de fontes.
- Regras de privacidade, denominadores, domínio de respostas e limites de comparação documentadas.

## Confirmações antes da análise ou publicação

| Item | Como será tratado até confirmação | Impacto |
| --- | --- | --- |
| Três respostas fora de Sim/Não em Q07 | Preservar original, booleano ausente e exclusão do denominador válido. | Não interpretar como Sim/Não nem deslocar entre perguntas. |
| Uma expectativa salarial sinalizada | Preservar R$5 e pedir confirmação; não converter para milhares. | Estatísticas de expectativa usam filtro documentado e análise de sensibilidade. |
| Um intervalo de experiência | Guardar limites, deixando meses exatos ausentes. | Não usar como valor pontual em correlação ou regressão. |
| Âncoras da escala Q05 | Mostrar apenas distribuição das notas até conferir o formulário. | Não interpretar direção nem construir indicador de satisfação. |
| Método de recrutamento | Registrar protocolo real da coleta. | Não afirmar representatividade estatística. |
| Consentimento e divulgação | Respostas individuais locais, ignoradas pelo Git. | Não publicar microdados; revisar agregados antes de divulgação. |
| Percentuais e afirmações da matriz | Manter como declarações e referências a verificar. | Não usá-los como evidência quantitativa confirmada do projeto. |

Esses itens são limites de execução explícitos, não lacunas nas perguntas ou nas
métricas do plano. Não há resultados inferenciais nem desempenho de modelos
inventados. Sem confirmação das escalas e consentimento, restringir a análise
às formas previstas neste documento e manter a divulgação bloqueada.

## Verificação técnica

O pipeline mantém SHA-256 dos XLSX, concilia linhas e colunas de CSV/Parquet,
preserva as respostas originais e os hyperlinks da matriz, valida prioridades
sem quebrar vírgulas internas e mantém intervalos de experiência sem imputação.
Os testes unitários cobrem conversões, respostas inválidas e limites de opções.

Os resultados estão em
[validação do pacote](../datasets/qualidade/validacao_exports.json) e
[validação da pesquisa](../datasets/qualidade/validacao_pesquisa_grupo12.json).
Passar na validação estrutural não remove os alertas semânticos.
