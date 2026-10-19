# Conferência da Etapa 05

Execução verificada em 19 de outubro de 2026. Entrega CC05: avaliação visual de
classificadores simples com métricas e implicações práticas interpretadas.
O atendimento técnico/documental não equivale à aprovação da professora.

## Critérios e Evidências

| Critério | Evidência | Situação |
| --- | --- | --- |
| Dados reais e alvo definido | State of Data, quatro respostas mapeadas, ausentes excluídos | Atendido |
| Treino e teste separados | 3.787/947 respostas, estratificação e semente 12 | Atendido |
| Classificadores simples e referência | Majoritária, logística e árvore de profundidade máxima 4 | Atendido |
| Matriz de confusão | C3: três matrizes com contagens e percentual por classe observada | Atendido |
| Acurácia, precisão, recall e F1 | C1/C2: tabela completa, gráfico e interpretação da classe positiva 1 | Atendido |
| ROC | C4: probabilidades da classe 1, curvas e ROC-AUC | Atendido |
| Precision-recall | C5: curvas, Average Precision e referência de prevalência | Atendido |
| Implicações práticas | C2/C3: baixo recall, falsos positivos/negativos e limites de uso | Atendido |
| Escolha sem consultar o teste | C1: maior AP média nos cinco folds do treino; limiar 0,5 fixo | Verificado |
| Diagnósticos adicionais | C6: limiares apenas OOF do treino; C7: calibração descritiva | Atendido |
| Rastreabilidade | Hash da fonte, código, produtos, versões e auditoria | Verificado |
| Privacidade e fontes separadas | Nenhum CAGED/G12; escores individuais somente locais | Verificado |

## Resultado Desta Execução

- 4.734 respostas elegíveis; 1.630 positivas e 3.104 negativas. Alvo ausente: 342.
- Escolhido pela validação no treino: regressão logística, AP média 0,448.
- Teste da logística, limiar 0,5: acurácia 0,661; precisão 0,532; recall 0,129;
  F1 0,207; ROC-AUC 0,601; Average Precision 0,435.
- Confusão da logística: TN=584, FP=37, FN=284, TP=42.
- A referência majoritária tem acurácia 0,656, mas recall/F1 iguais a zero.
- A logística deixa de identificar 87,1% das buscas ativas: o desempenho é limitado,
  não valida detecção individual e não foi artificialmente melhorado no teste.
- Pernambuco tem somente 17 respostas no teste; métricas locais suprimidas.
- Sete figuras, 13 CSV agregados, auditoria, notebook executado e HTML independente.
- 24 testes novos passaram: alvo, cobertura, vazamento, métricas, seleção,
  partições, OOF, hashes, notebook e imagens incorporadas.

Os números acima são um registro desta execução. Notebook, `sintese_achados.md`
e `registro_execucao.json` são gerados pelo runner e prevalecem após nova execução.

## Revisão Visual e Limites

Sete figuras revisadas: equilíbrio das classes, comparação de métricas, matrizes,
ROC, PR, limiares e calibração. Rótulos, unidades, denominadores e notas conferidos.
As curvas usam escores, não somente classes já cortadas. AP não é apresentada
como área trapezoidal genérica. Ausência não equivale a classe 0.

Sem validação temporal/externa, inferência causal ou representatividade de toda TI.
Há viés de elegibilidade por ramificação do formulário e senioridade ausente.
Não usar para monitorar empregados ou decidir contratação/desligamento.
IDs e probabilidades por resposta ficam locais, ignorados pelo Git.
Nenhum dado original foi regravado, nenhum modelo foi integrado ao aplicativo
e nenhum commit/publicação foi realizado. A etapa 06 segue pendente.
