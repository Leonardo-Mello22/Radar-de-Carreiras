# Conferência da Etapa 04

Execução verificada em 19 de outubro de 2026. Entrega CC04: notebook de
visualizações apoiado por regressão simples, com dispersão, tendência e resíduos.
O atendimento documental e técnico não representa aprovação da professora.

## Critérios e Evidências

| Critério | Evidência | Situação |
| --- | --- | --- |
| Notebook de visualizações | `resultados/regressao_salarial_executada.ipynb`, 12 células de código executadas sem erro | Atendido |
| Modelo simples de regressão | Regressão linear por idade; comparação adicional com Ridge linear de cinco entradas | Atendido |
| Dispersão e linha de tendência | R2: amostra visual de março, reta aprendida em janeiro-fevereiro, medianas por idade | Atendido |
| Observados e previstos | R3: densidade em hexágonos e diagonal de igualdade, sem ajuste no teste | Atendido |
| Análise de resíduos | R4: resíduos versus previsão, histograma completo e quantis interpretados | Atendido |
| Referência simples | Mediana do treino, comparada nos mesmos 19.825 eventos reservados | Atendido |
| Métricas interpretadas | MAE/RMSE/R², validação interna, comparação final e limitações em R1/R5 | Atendido |
| Comunicação de relações e padrões | R2-R8: tendência, dispersão, caudas, calibração e diferenças de composição | Atendido |
| Controle de vazamento | Lista explícita de entradas, partição temporal, transformações aprendidas no treino | Verificado por testes |
| Reprodutibilidade | Runner, versões, integridade da fonte, hashes dos produtos e 17 testes | Verificado |

## Resultado da Execução

- 60.862 admissões com salário válido; 41.037 para ajuste final e 19.825 no teste.
- Escolha feita na validação janeiro->fevereiro: regressão linear múltipla com Ridge.
- Teste de março: MAE de R$2.666,77 contra R$3.734,23 da mediana do treino,
  redução de 28,6%. RMSE de R$4.306,95 e R² de 0,476.
- 255 previsões negativas, mantidas e explicitadas como limite do modelo linear.
- Seis figuras, 14 CSV, auditoria de modelagem, notebook executado e HTML independente.
- 17 testes da etapa passaram: regras, seleção, integridade, reconciliação de métricas,
  cobertura dos recortes, imagens não vazias e incorporação das imagens no HTML.

Esses números são um registro desta execução. A fonte para resultados atualizados
é o notebook, `sintese_achados.md` e `registro_execucao.json`, gerados pelo runner.

## Revisão e Limites

Gráficos revisados visualmente: rótulos, escalas, legendas, fontes e notas.
O teto p99 é somente visual; todos os salários válidos entram nas métricas.
Nos resíduos, a amplitude completa é mostrada. Os CSV públicos são agregados,
sem identificadores de evento. As previsões por linha e os caches ficam locais,
ignorados pelo Git. Não há dados G12 nesta etapa.

O ganho global não valida uma calculadora salarial pessoal. Um único mês de teste,
previsões negativas, erros de cauda e ausência de identificação longitudinal limitam
o uso. Não há causalidade, senioridade inferida, crescimento individual ou salários
atuais de 2026. Não houve integração automática ao dashboard. A etapa 05 segue pendente.
