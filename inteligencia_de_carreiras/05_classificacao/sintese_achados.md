# Sintese da classificacao de busca ativa

Etapa 05. State of Data Brazil 2024-2025; avaliacao de intencao declarada, nao de desligamento futuro.

## C0

Dos 5,076 residentes no Brasil, 342 nao tem alvo respondido e nao recebem classe 0. Restam 4,734 respostas, 1,630 positivas (34.4%). A separacao estratificada, semente 12, reserva 947 respostas para teste e 3787 para treino. A classe 0 inclui pessoas abertas a oportunidades, mas que nao declaram busca ativa. O alvo e intencao contemporanea, nao mudanca de emprego futura. As ausencias se concentram em ramos do questionario; os elegiveis nao representam todos os desempregados ou toda a populacao de TI. Senioridade ausente nao vira Junior. Vinculo agrupado remove mencoes de busca presentes no texto bruto.

## C1

A escolha feita somente no treino foi **Regressao logistica**, com Average Precision media 0.448 em cinco folds (desvio entre folds 0.014, nao intervalo de confianca). Cada fold ajusta imputacao, categorias e modelo apenas nos seus dados de treino. A referencia aprende a proporcao das classes no treino e decide a classe majoritaria. Os tres modelos sao depois reajustados nos 80% e avaliados nos mesmos 20% reservados. C, profundidade e tamanho minimo de folha sao fixos; limiar 0,5 definido previamente, sem otimizacao. O teste nao decide modelo, hiperparametros ou limiar. As probabilidades OOF sao usadas apenas para diagnostico interno.

## C2

A referencia acerta 65.6% simplesmente escolhendo a classe 0, mas nao identifica nenhuma busca ativa: recall e F1 iguais a zero. Por isso acuracia sozinha seria enganosa. O modelo escolhido tem acuracia 0.661, precisao 0.532, recall 0.129 e F1 0.207 no limiar 0,5. Precisao descreve a fracao correta entre positivos previstos; recall, a fracao de buscas ativas identificadas. Precisao sem positivos previstos e registrada como 0 por convencao zero_division=0, nao como evidencia de taxa populacional. F1 combina precisao e recall, mas ignora os verdadeiros negativos. O escolhido deixa de identificar 87.1% dos positivos; este desempenho e limitado e nao valida uma ferramenta de deteccao individual. O limiar nao foi alterado para melhorar os resultados do teste.

## C3

Para Regressao logistica, ha 42 verdadeiros positivos, 284 falsos negativos, 37 falsos positivos e 584 verdadeiros negativos. Um falso negativo e uma pessoa que declara busca ativa e recebe classe 0; um falso positivo recebe classe 1 sem declarar busca ativa. As porcentagens usam a classe observada como denominador e cada linha soma 100%; as contagens preservam o tamanho real das classes. Esses erros impedem usar a classificacao para rotular empregados ou orientar decisoes de contratacao, desligamento ou vigilancia.

## C4

O modelo previamente escolhido tem ROC-AUC 0.601. A curva usa escores/probabilidades, nao somente as classes do limiar 0,5; mostra o compromisso entre falsos positivos e recall. A referencia constante tem AUC 0,5. AUC e capacidade de ordenacao, nao acuracia, probabilidade de acerto individual ou prova de causalidade. A classe positiva e 1 em todos os calculos. O teste e uma avaliacao da mesma pesquisa, nao validacao temporal externa.

## C5

Average Precision (AP) do escolhido: 0.435; referencia constante: prevalencia de 0.344. AP resume a curva ponderando os incrementos de recall e nao e a area trapezoidal generica sob a PR. A leitura considera que buscas ativas sao a classe minoritaria. Ganhar recall costuma incluir mais falsos positivos. O ultimo ponto convencional da curva tem precisao 1 e recall 0, sem observacoes previstas positivas; nao prova um classificador perfeito. A precisao e a AP dependem da prevalencia, portanto nao podem ser transferidas diretamente para outra populacao.

## C6

Esta curva usa somente previsoes out-of-fold do treino: cada linha foi prevista por um pipeline que nao a usou no ajuste daquele fold. O modelo foi selecionado com os mesmos folds, portanto a curva e um diagnostico interno e pode ser otimista. Limiar 0,5 permanece fixo; nenhum ponto foi escolhido por maximizar F1 nesta curva ou no teste. Reduzir o limiar tende a ampliar recall e alertas falsos; aumentar pode deixar mais buscas ativas sem identificacao. Uma alteracao futura exige objetivo/custos definidos e nova validacao, nao reutilizar este teste como treino.

## C7

Brier score do escolhido: 0.220 (menor e melhor). O grafico agrupa probabilidades do teste em cinco intervalos fixos e mostra apenas faixas com n>=30; nao recalibra o modelo. Distancia da diagonal representa diferenca entre escore medio e frequencia observada. As probabilidades nao foram calibradas externamente e nao sao riscos pessoais comprovados de demissao ou mudanca futura. Discriminacao e calibracao sao conceitos distintos.

## C8

Pernambuco tem n=17 no teste; n<30, portanto suas metricas foram suprimidas. Brasil/NE/PE sao recortes aninhados, nao somaveis. A tabela por vinculo evidencia quem ficou sem alvo, reforcando o vies de elegibilidade do questionario; a exclusao nao equivale a nao buscar emprego. Nulos de senioridade podem vir de ramificacoes do formulario, inclusive gestao: nao representam senioridade baixa. Categorias novas do teste sao ignoradas pelo encoder sem ajustar novamente. Nao foi feita auditoria de equidade, validacao com outra pesquisa ou avaliacao temporal externa. Nao aplicar estes modelos para rotular pessoas em decisoes laborais.

## Uso e limites

Estudo exploratorio com pesquisa voluntaria e um teste estratificado da mesma coleta. Nao representa todos os profissionais de TI, nao identifica causalidade e nao valida uso em contratacao, demissao, monitoramento de empregados ou aconselhamento individual automatizado. Nenhuma fonte CAGED ou G12 foi adicionada. Probabilidades por participante ficam locais; resultados versionaveis sao agregados. A etapa 06 ainda exige integracao, narrativa, usabilidade e revisao de privacidade; nenhum classificador foi integrado automaticamente ao aplicativo.
