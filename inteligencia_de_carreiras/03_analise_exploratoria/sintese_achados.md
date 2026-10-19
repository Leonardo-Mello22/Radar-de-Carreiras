# Síntese da análise exploratória

Resultados das fontes públicas, separados por unidade e período. Não inclui dados da pesquisa própria.

## P1

Entre 60.862 admissões com salário válido, a mediana de Pernambuco é R$ 3.165, contra R$ 3.520 no Brasil; a faixa p10-p90 de PE vai de R$ 1.600 a R$ 10.799. Esses recortes são aninhados, não amostras independentes. A diferença agregada também reflete composição de cargos; não estima salário júnior nem efeito causal da região. A tabela por área só divulga quantis com n>=30.

## P2

No Brasil, os arquivos MOV somam 61.047 admissões e 57.517 desligamentos, diferença de 3.530. Em PE, a diferença MOV é 263. Salários sinalizados continuam nessas contagens. Não há ajustes FOR/EXC, portanto não chamar essa diferença de saldo oficial final. Três meses não permitem concluir sazonalidade ou tendência anual; os painéis usam escalas próprias.

## P3

Foram encontrados 250 pares UF/CBO/mês com pelo menos 30 salários válidos em cada movimento; 11 estão em PE. Entre os pares de PE, 4 apresentam mediana de admissão maior e 7 menor que a de desligamento. O gráfico mostra os oito pares de maior cobertura. Mesmo com cargo, UF e mês equivalentes, são pessoas diferentes: a diferença não mede aumento salarial, promoção ou trajetória individual.

## P4

A correlação de Spearman entre idade e salário é 0.510, com 60.862 pares; para jornada é -0.054. Em 91 grupos CBO/UF com n>=100 e variação, a mediana do rho idade-salário é 0.426. A análise dentro desses recortes reduz parte da mistura de cargos/regiões, mas não controla todos os fatores. Diferenças por escolaridade e idade não demonstram retorno causal da formação nem senioridade.

## M1

O agrupamento considera 67 perfis UF/área, cobrindo 57.702 de 60.862 admissões válidas (94,8%). Cada perfil tem ao menos 100 salários, 100 jornadas e 100 escolaridades informadas. As três dimensões são log da mediana salarial, proporção de formação superior e média de jornada, padronizadas por z-score. Entre k=2 a 5, k=5 maximiza silhouette (0.410); a concordância entre sementes 12/13 é ARI=1.000. Cada perfil tem o mesmo peso no ajuste, não cada pessoa. Grupos são descritivos e seus números arbitrários; não são classes de trabalhadores, previsão, ranking de regiões ou evidência causal. A escolha está limitada à faixa de k explorada e não valida a existência de cinco grupos naturais. A projeção exibe apenas duas das três dimensões.

## P5

Os recortes têm 855 júniores declarados, 185 estagiários e 1490 participantes com até dois anos em dados. Há sobreposição: estágio, nível declarado e experiência em dados não são coortes mutuamente exclusivas nem equivalentes. As composições de formação, vínculo e trabalho usam denominador próprio de resposta informada, com cobertura registrada nas tabelas.

## P6

Há 4.734 respostas salariais entre 5.076 residentes no Brasil; a faixa mais frequente é 'de R$ 8.001/mês a R$ 12.000/mês'. Os mapas mostram a composição dentro de cada nível, cargo ou modelo de trabalho, com n>=30 por linha. Cargo exibe os seis de maior cobertura, não todos. Distribuições entre grupos não estimam efeito causal do remoto ou retorno da senioridade; nenhuma faixa foi convertida em ponto médio, média salarial ou valor individual exato.

## P7

Entre os itens selecionados, SQL tem a maior proporção declarada (87,7%, 3.070/3.502 respostas válidas). Os denominadores variam entre SQL/linguagens, BI e nuvem pela ramificação do questionário. Ausente não foi convertido em Não. A tabela por área mantém apenas proporções com n>=30 no item. Selecionar tecnologia não mede vagas abertas nem demanda empresarial; percentuais de várias tecnologias podem somar mais de 100%.

## P8

O alvo tem 4.734 respostas válidas: 1.630 de busca ativa (34,4%) e 3.104 sem busca ativa. As 342 ausências não viram negativas. As tabelas mostram associações descritivas por perfil com denominador válido. Não foi treinado classificador nesta etapa: matriz de confusão, ROC e F1 pertencem à fase 05. Busca declarada não é desligamento futuro.

## Limites gerais

Associações não demonstram causalidade; movimentações não identificam pessoas. Recortes regionais se sobrepõem. A amostra State of Data é voluntária; carreira em dados não representa toda TI. A matriz de desk research não foi tratada como evidência verificada. Modelos de regressão e classificação serão desenvolvidos nas fases seguintes.
