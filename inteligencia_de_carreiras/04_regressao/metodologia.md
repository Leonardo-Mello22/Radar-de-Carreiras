# Metodologia da Regressão

Etapa 04. Versão 1.0. 19 de outubro de 2026. Protocolo derivado da etapa 01.

## Universo e Alvo

- Fonte: `datasets/tratados/caged_ti.parquet`, com integridade verificada contra
  `datasets/qualidade/execucao_preparacao.json` antes da leitura analítica.
- Unidade: movimentação de admissão, selecionada por `saldo=1` e `salario_valido=True`.
- Alvo: `salario_real`, salário mensal em R$ a preços de março de 2025, já preparado
  por `nominal × IPCA(março) / IPCA(competência)`. Não converter novamente por horas/dias.
- Salários sinalizados ficam fora da regressão, mas permanecem na fonte e nas contagens
  gerais. Todos os salários válidos são usados, inclusive os extremos.
- O recorte CBO e os limites de validade são os documentados nas etapas 01 e 02.
  Não há reclassificação de ocupações ou alteração dos dados preparados nesta etapa.

## Partições e Escolha

| Finalidade | Ajuste | Avaliação | Uso |
| --- | --- | --- | --- |
| Validação interna temporal | Janeiro/2025 | Fevereiro/2025 | Escolher menor MAE entre os três modelos definidos |
| Ajuste final | Janeiro-fevereiro/2025 | Nenhuma observação de março | Reestimar os três modelos com mais dados |
| Teste reservado | Nenhum ajuste | Março/2025 | Medir desempenho e produzir diagnósticos |

Não há separação aleatória. Em empate, a ordenação fixa favorece mediana, depois
idade, depois múltipla. Março não decide modelo, regularização, colunas, imputação,
codificação ou escala. Os modelos são comparados no teste para transparência,
não para uma nova escolha. Cada validação começa com um pipeline novo.

O IPCA de referência comum é uma convenção monetária retrospectiva; a análise
não simula disponibilidade de índices econômicos em tempo real em janeiro.
Não se reivindica independência entre eventos nem exclusividade de pessoas entre
meses: não há identificador de pessoa, estabelecimento ou vínculo neste pacote.
Linhas de eventos semelhantes não são removidas automaticamente.

## Entradas e Pré-processamento

| Campo | Regra |
| --- | --- |
| Idade | Valor numérico apenas com `idade_valida=True`; caso contrário, ausente |
| Horas contratuais | Valor numérico apenas com `horas_validas=True`; caso contrário, ausente |
| Numéricas ausentes | Mediana do treino; indicador de ausência quando houver ausência no treino |
| Numéricas completas após imputação | `StandardScaler` ajustado no treino; nenhum ajuste no teste |
| CBO, UF e escolaridade | Categorias nominais com one-hot; sem ordem numérica arbitrária |
| Categoria ausente | Token explícito `Nao informado`, sem usar o salário |
| Categoria não vista no treino | `handle_unknown=ignore`; zeros nesse bloco; cobertura registrada |
| Demais campos | Excluídos por lista explícita das cinco entradas permitidas |

Não usar `salario_nominal`, `salario_fixo_declarado`, faixas ou escalas do alvo.
IDs, arquivo de origem e competência servem apenas para auditoria/partição.
Área de TI e região servem apenas para avaliação dos recortes. Sexo e raça/cor
não entram no modelo inicial. Sua exclusão não remove vieses ou proxies e não
constitui auditoria de equidade. Nenhuma fonte externa é juntada por participante.

## Modelos Simples

| Modelo | Definição | Objetivo |
| --- | --- | --- |
| Mediana | Valor constante: mediana salarial do treino | Referência adequada ao erro absoluto |
| Linear por idade | Mínimos quadrados, intercepto e idade padronizada | Representar uma tendência marginal visual |
| Linear múltipla | Ridge, `alpha=10`, intercepto, numéricas e categorias codificadas | Explorar associações condicionais sem modelo não linear complexo |

Alpha é fixo e não otimizado no teste; a penalização estabiliza a codificação
one-hot completa. Essa escolha não garante o melhor modelo possível e não foi
feita para maximizar a nota das métricas. Todas as previsões são mantidas, inclusive
eventuais valores negativos, cuja contagem é registrada. Não há correção posterior.

Os coeficientes exportados estão na escala da matriz codificada: numéricas
padronizadas, indicadores e one-hot. Não há uma categoria-base omitida na Ridge.
Sua leitura deve considerar intercepto, penalização e composição das entradas,
sem interpretar os valores como efeitos causais ou diferenças salariais individuais.
A inclinação simples da idade é também registrada na unidade original R$/ano.

## Métricas e Diagnósticos

Resíduo: `observado - previsto`. Positivo significa subestimação.

- MAE: média do valor absoluto do resíduo; critério primário de escolha.
- RMSE: raiz da média do quadrado do resíduo; sensível às caudas.
- R²: comparação quadrática com a média observada no conjunto de avaliação;
  pode ser negativo e não prova causalidade.
- Erro absoluto mediano, média do resíduo e quantidade de previsões negativas:
  diagnóstico complementar, sem ocultar resultados desfavoráveis.

Métricas de UF e área exigem n>=30, regra operacional de cobertura, não garantia
de representatividade. O n é mantido para os grupos suprimidos. Brasil, Nordeste
e Pernambuco se sobrepõem e nunca são somados.

Dispersão por idade usa uma amostra visual fixa de até 6.000 eventos de março,
semente 12; a reta vem do treino final. As medianas por idade em março são
descritivas e exigem n>=30. O teto visual é o p99 salarial do treino, fixado antes
do teste; a quantidade de pontos fora da janela aparece no gráfico.

Observado versus previsto usa densidade de hexágonos com janela p99 do treino.
Resíduos e histograma mostram a amplitude completa, sem truncamento. Calibração
agrupa as previsões de março em quantis apenas para diagnóstico, sem recalibrar.
As barras p10-p90 são dispersão observada, não intervalos de confiança ou previsão.

A sensibilidade separa salários observados acima/abaixo do p99 do treino. É uma
leitura posterior de erros, não regra de filtragem futura. A avaliação principal
mantém toda a amostra elegível; não há winsorização ou remoção baseada no teste.

## Limitações e Rastreabilidade

O estudo cobre admissões formais no recorte de TI do primeiro trimestre de 2025.
Não inclui PJ/informalidade, habilidades, senioridade, tempo de vínculo ou trajetórias.
Um único mês de teste não demonstra estabilidade temporal, sazonalidade ou desempenho
no mercado atual. Linearidade pode representar mal relações e caudas salariais.
Heterocedasticidade e assimetria podem permanecer; não foram estimados p-valores
ou intervalos baseados em normalidade e independência não demonstradas.

`registro_execucao.json` registra versões, hashes do código, da fonte, das tabelas,
dos gráficos e dos notebooks. `resultados/auditoria_modelagem.json` registra a
escolha anterior ao teste, medianas, categorias aprendidas e limiar visual.
O extrato linha a linha fica em `resultados_locais/`, ignorado pelo Git; saídas
versionáveis contêm agregados da fonte pública. O pipeline original e os dados
preparados não são regravados. A etapa 05 e a integração no dashboard são futuras.
