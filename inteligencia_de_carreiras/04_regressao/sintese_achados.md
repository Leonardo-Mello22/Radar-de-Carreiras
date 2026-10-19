# Sintese da regressao salarial

Etapa 04. Radar de Carreira em TI. Execucao com CAGED MOV de jan-mar/2025.

Somente fontes publicas; sem State of Data ou pesquisa G12. Valores mensais a precos de marco/2025.

## R0

Dos 118.564 movimentos, ha 61.047 admissoes. A modelagem usa 60.862 salarios validos; 185 salarios sinalizados ficam fora desta tarefa, sem alterar a fonte. Treino final: 41.037 eventos de jan-fev; teste final: 19.825 de marco. Idade e horas invalidas viram ausentes nas entradas, sem excluir eventos; imputacao, escala e categorias sao ajustadas somente no treino. Linhas de eventos semelhantes sao preservadas: nao existe identificador de pessoa/vinculo. Nenhum dado de State of Data ou G12 entra nesta etapa.

## R1

A validacao jan->fev escolheu **Linear: cinco variaveis**, antes do teste. Todos os modelos foram depois reajustados em jan-fev. Em marco, o modelo escolhido tem MAE R$ 2.667, RMSE R$ 4.307 e R2=0.476. A referencia constante usa apenas a mediana de jan-fev (R$ 3.520). MAE foi definido para a escolha; a mediana minimiza erro absoluto, nao erro quadratico. A regressao simples usa idade; a multipla e linear com penalizacao Ridge fixa alpha=10, sem busca de hiperparametros. Março nao ajusta imputacao, escalas, categorias, coeficientes, alpha ou escolha de modelo. Previsoes negativas, se houver, nao sao recortadas.

## R2

A reta simples ajustada em jan-fev varia R$ 259 por ano de idade. Isso e associacao marginal, nao efeito causal, experiencia profissional ou crescimento individual. A mediana por idade em marco nao e a reta OLS, que aproxima a media condicional sob especificacao linear. O teto do grafico e o p99 do salario do treino; 33 dos 6000 pontos da amostra visual ficam acima dele. Todos os registros entram nas metricas e nos residuos.

## R3

A diagonal representa previsao exata. Concentracao sistematica acima da diagonal indica subestimacao. O grafico compara os dois regressores, sem escolher pelo teste; usa densidade em hexagonos e janela limitada pelo p99 do treino nos dois eixos. O numero fora da janela e informado por modelo, sem exclui-lo da avaliacao. A regressao linear pode comprimir a dispersao e errar salarios altos: ela nao fornece um intervalo salarial individual confiavel.

## R4

Para Linear: cinco variaveis, o residuo observado-previsto tem mediana R$ -320, p10 R$ -3.856 e p90 R$ 4.312. Residuo positivo significa subestimacao; negativo, superestimacao. Ambos os paineis incluem a amplitude completa, sem corte de cauda. Assimetria, caudas e variacao da dispersao indicam limites da aproximacao linear; nao se presume normalidade, homocedasticidade ou independencia entre eventos. Nao foram calculados p-valores, intervalos de confianca ou de previsao.

## R5

No teste, a mediana do treino tem MAE R$ 3.734; o modelo previamente escolhido tem MAE R$ 2.667, variacao de 28.6% em relacao a referencia (positivo = reducao). Seu RMSE e R$ 4.307, metrica mais sensivel a erros extremos. Foram geradas 255 previsoes negativas (1.3% do teste), valores sem sentido salarial, mantidos para expor o limite da forma linear. Isso impede tratar a melhoria global como validacao de uma calculadora salarial individual; nenhum valor foi corrigido apos olhar o teste. A tabela inclui R2 e erro absoluto mediano. Desempenho em um unico mes nao demonstra generalizacao para 2026 ou outros mercados. Nao houve reescolha de modelo a partir deste grafico.

## R6

Em Pernambuco, o modelo escolhido tem MAE R$ 2.299 em 399 admissoes de marco. Ha 3 recortes UF/area com n<30 e metricas suprimidas (o n permanece). A referencia usada por regiao continua sendo a mediana global do treino, nao uma mediana local recalculada no teste. Brasil, Nordeste e PE sao recortes aninhados e nao devem ser somados. Diferencas refletem composicao de cargos e salarios; nao constituem auditoria de equidade nem avaliacao individual. Tabelas completas por UF e area acompanham o notebook.

## R7

As faixas usam os quantis das previsoes de marco apenas para diagnostico, sem novo ajuste ou calibracao. A curva aproxima medias previstas e observadas; as faixas verticais sao p10-p90 dos salarios observados, nao intervalos de confianca/previsao. Distancia da diagonal revela erro medio sistematico; a largura da faixa mostra variacao de salarios entre eventos com previsoes semelhantes. Nao se recomenda esse modelo como calculadora salarial pessoal.

## R8

O limiar p99 foi fixado no treino (R$ 28.526). Na cauda acima dele ha 173 eventos, com MAE R$ 22.599, contra R$ 2.491 abaixo/igual ao limiar. Esta e uma analise de sensibilidade por salario observado, nao um filtro de producao: o alvo futuro nao estaria disponivel para decidir a faixa. A avaliacao principal mantem todos os salarios validos e nao usa winsorizacao ou remocao de outliers baseada em marco. Categorias novas sao codificadas com zeros pelo encoder; a tabela informa sua cobertura. Os coeficientes sao descritivos: numericas estao padronizadas e categorias usam one-hot completo com Ridge, sem categoria-base omitida. Nao sao retornos causais da escolaridade, premios salariais individuais ou medidas de significancia.

## Limites e proximo passo

Estudo observacional de movimentacoes, nao pessoas ou vinculos. Apenas um mes reservado para teste; nao permite previsao de longo prazo ou inferencia causal. Nao identifica senioridade, habilidades, tempo de vinculo ou evolucao individual. A exposicao da fonte e real de mar/2025 (IPCA comum), nao informacao de salario atual de 2026. Sexo e raca/cor nao entram; isso nao elimina vieses ou proxies. A etapa 05 continua pendente e usa outra fonte/alvo.
