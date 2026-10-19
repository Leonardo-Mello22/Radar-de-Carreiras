# Metodologia da Classificação

Etapa 05. Versão 1.0. 19 de outubro de 2026. Protocolo da etapa 01, com decisões
operacionais explícitas antes da leitura do desempenho no teste.

## Fonte, Universo e Alvo

Fonte única: `datasets/tratados/state_of_data_brasil.parquet`, conferida por
SHA-256 contra `datasets/qualidade/execucao_preparacao.json`. A preparação já
removeu duas linhas integralmente repetidas na pesquisa pública original.
Não remover participantes apenas por terem perfis iguais nas cinco entradas.
O ID identifica a linha tratada; não comprova que cada linha seja uma pessoa única.

Universo: residentes no Brasil com `planos_mudar_emprego_6m` respondido.

| Classe | Resposta original |
| --- | --- |
| 1: busca ativa | Estou em busca de oportunidades dentro ou fora do Brasil |
| 1: busca ativa | Estou em busca de oportunidades, mas apenas fora do Brasil |
| 0: sem busca ativa | Não estou buscando, mas me considero aberto a outras oportunidades |
| 0: sem busca ativa | Não estou buscando e não pretendo mudar de emprego nos próximos 6 meses |
| Sem alvo | Excluir da tarefa supervisionada; nunca converter em classe 0 |

Uma nova resposta fora dessas quatro opções interrompe o pipeline para revisão.
São 4.734 elegíveis entre 5.076 residentes: 1.630 positivos e 3.104 negativos;
342 não têm o alvo. Classe 0 não significa rejeitar qualquer oportunidade.
O alvo é declaração contemporânea, não mudança futura observada.

## Viés de Elegibilidade

O item está ausente em ramos do formulário, incluindo muitos desempregados,
estudantes e pessoas da área acadêmica. A tabela de ausências por vínculo registra
esse padrão. Não inferir a resposta de quem não respondeu e não completar o alvo
com a informação de busca presente em outras perguntas.

Consequentemente, os elegíveis não representam toda a população desempregada nem
todos os profissionais de TI. A coleta é voluntária, específica da área de dados
e referente a 2024-2025, não ao mercado atual de 2026.

## Entradas Permitidas

| Campo | Tratamento e limite |
| --- | --- |
| `senioridade_declarada` | Categoria nominal; ausência pode representar ramificação/gestão, não Júnior |
| `nivel_ensino` | Categoria nominal; nenhuma ordem numérica artificial |
| `vinculo_grupo` | Agrupamento já preparado; remove distinções de busca presentes no texto bruto de situação laboral |
| `modelo_trabalho_declarado` | Preservar as categorias declaradas, inclusive modalidades híbridas distintas |
| `experiencia_dados_faixa` | Faixa nominal; não usar ponto médio nem confundir com toda a experiência profissional |

Lista de entradas explícita, sem seleção automática de outras colunas. Ausências
viram uma categoria constante `Nao informado`, não zero ou classe majoritária.
One-hot aprende categorias somente no treino e ignora categorias novas no teste,
sem ajustá-las novamente. A cobertura de categorias novas é registrada.

Excluir a pergunta-alvo, cópias, entrevistas recentes, oportunidade buscada, tempo
de busca e objetivo de carreira. O texto bruto `situacao_trabalho` pode mencionar
busca e não entra: apenas o vínculo neutro agrupado. Salário, satisfação, gênero,
raça/cor, localização e outros campos ficam fora do primeiro modelo. Essa exclusão
não elimina vieses ou proxies e não constitui auditoria de equidade.

## Separação, Validação e Modelos

1. Separar índices antes de ajustar qualquer transformação: teste estratificado
   de 20%, semente 12. Treino: 3.787; teste: 947. IDs não se sobrepõem.
2. Dentro dos 80%, fazer cinco folds estratificados, embaralhamento e semente 12.
   Cada fold ajusta seu próprio pipeline somente na porção de treino do fold.
3. Comparar três candidatos predefinidos, sem busca de hiperparâmetros.
4. Escolher a maior Average Precision média nos folds. Empate favorece a referência,
   depois logística, depois árvore. Desvio entre folds não é intervalo de confiança.
5. Reajustar os três pipelines nos 80% completos e avaliar nos mesmos 20% reservados.
   Não escolher novamente pelo teste. Limiar 0,5 fixo, definido antes da avaliação.

| Modelo | Configuração |
| --- | --- |
| Classe majoritária | `DummyClassifier(strategy=prior)`; classe mais frequente e probabilidade constante aprendida no treino |
| Logística | Regularização L2 padrão, C=1, solver `lbfgs`, até 2.000 iterações |
| Árvore simples | Profundidade máxima 4, mínimo 40 observações por folha, semente 12 |

Sem balanceamento artificial, pesos de classe, SMOTE ou dados G12 adicionados.
Nenhum ajuste aprende com o teste. Não há junção de pessoas entre fontes.
Perfis iguais em entradas categóricas não provam duplicação ou vazamento de pessoas.
A ausência de um identificador pessoal real impede garantir independência absoluta
de participantes; o teste é uma separação de respostas da mesma coleta.

## Métricas e Leitura

Classe positiva = 1. Limiar: `probabilidade(1) >= 0,5`.

- Matriz de confusão: linhas observadas, colunas previstas; ordem 0, 1.
  TN/FP na primeira linha e FN/TP na segunda. Mostrar contagens e percentual por linha.
- Acurácia: `(TP+TN)/n`. Pode favorecer um modelo que sempre escolhe a classe 0.
- Precisão: `TP/(TP+FP)`. Sem positivos previstos, valor 0 por convenção explícita
  `zero_division=0`, não evidência de uma taxa populacional conhecida.
- Recall: `TP/(TP+FN)`. Mostra a cobertura das buscas ativas realmente declaradas.
- F1: média harmônica de precisão e recall; não considera diretamente TN.
- ROC e ROC-AUC: calculadas com probabilidades da classe 1, não classes já cortadas.
  AUC é ordenação/discriminação, não acurácia nem prova de causalidade.
- Precision-recall e Average Precision: AP pondera incrementos de recall;
  não é simplesmente área trapezoidal sob a curva. A referência constante tem
  AP igual à prevalência do positivo no conjunto avaliado.
- Brier score: média do erro quadrático entre probabilidade e alvo; diagnóstico
  complementar. Menor é melhor, mas não comprova calibração em outra população.

Para subconjunto com apenas uma classe, ROC-AUC/AP ficam ausentes. Métricas de
subgrupos exigem n>=30; a regra é operacional, não garantia de representatividade.
Brasil/NE/PE são aninhados, não somáveis. O n permanece nos recortes suprimidos.

## Diagnósticos e Limites

O gráfico de limiar usa apenas probabilidades out-of-fold dos 80% de treino.
Cada resposta foi prevista por um pipeline que não a ajustou naquele fold, mas
a seleção usa os mesmos folds: a curva é diagnóstico interno sujeito a otimismo,
não estimativa final independente. Não se escolhe um limiar para maximizar F1 nela.
O limiar 0,5 é mantido no teste, inclusive quando o recall fica baixo.

Calibração descritiva: cinco intervalos fixos entre 0 e 1, calculados no teste
apenas para diagnóstico. Faixas com n<30 não exibem taxas. Nenhum recalibrador é
ajustado no teste. Escores não são riscos comprovados de saída de um empregado.

A acurácia pode melhorar pouco e o recall continuar baixo. Esses resultados são
reportados integralmente, sem reutilizar o teste para melhorar artificialmente
o desempenho. Uma mudança de modelo/limiar exigirá nova validação e avaliação.
Não há prova de generalização temporal, externa, causal ou de desempenho individual.
Não usar para monitorar trabalhadores ou decidir contratação/desligamento.

## Rastreabilidade e Privacidade

`registro_execucao.json` contém versões, hashes de código, fonte, gráficos,
tabelas, notebook e HTML. `resultados/auditoria_modelagem.json` registra a seleção,
configurações, categorias aprendidas e hashes dos conjuntos ordenados de IDs,
sem divulgar os próprios IDs. Previsões por resposta e OOF ficam apenas em
`resultados_locais/`, ignorada pelo Git; saídas versionáveis são agregadas.

O runner não modifica a fonte preparada, as etapas anteriores ou o dashboard.
Não publica arquivos nem cria commits. A etapa 06 é o trabalho de integração
e comunicação dos achados, com revisão própria de privacidade e usabilidade.
