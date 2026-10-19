# Plano de análise de carreiras

Radar de Carreira em TI. Grupo 12. CESAR School.
Etapa 01. Versão 1.1. 14 de outubro de 2026.

## 1 Escopo, fontes e objetivos

**Objetivo:** planejar análises que ajudem estudantes e profissionais iniciantes a compreender salários de contratação, movimentações do emprego formal e perfis da área de dados, com foco em Pernambuco e Nordeste.

### Problema e público

A hipótese de problema é que informações sobre o mercado de TI são fragmentadas e difíceis de comparar. O Radar pretende apoiar decisões de carreira. O grupo forneceu um questionário com 35 respostas, de estudantes de CC e Design; seus resultados ainda devem ser analisados e não são validação automática da hipótese.

### Pergunta central

Quais salários e fluxos aparecem no emprego formal de TI, que perfis são declarados na área de dados e quais dificuldades, prioridades e intenções os participantes da pesquisa própria relatam?

| Fonte e unidade | Recorte disponível | Uso previsto |
| --- | --- | --- |
| Novo CAGED: movimentação de admissão ou desligamento | Jan-mar/2025. Brasil: 118.564; Nordeste: 10.704; PE: 2.305. | Faixas salariais e fluxos de emprego formal. |
| State of Data: resposta de participante | 2024-2025. 5.215 respostas tratadas; 5.076 residentes no Brasil; PE: 120. | Perfis, formação, tecnologias e intenção de mudança. |
| Pesquisa G12: resposta ao questionário próprio | 35 respostas; 12 perguntas; coleta de 31/08 a 04/09/2026. | Necessidades, prioridades, expectativa e intenção de mudança. |
| IPCA e municípios do IBGE | IPCA jan-mar/2025, referência mar/2025; códigos municipais padronizados. | Comparabilidade monetária e geográfica. |

### Escopo do pacote

O CAGED foi filtrado pelas famílias 1236, 1425, 2122, 2123, 2124, 3171 e 3172, totalizando 27 ocupações. O agrupamento analítico de áreas está em **datasets/auxiliares/cbo_ti_categorias.csv**. Os números acima são inventário do pacote, não resultados das análises planejadas.

As fontes permanecem separadas, com catálogo único. A matriz G12 contém 21 referências/hipóteses, não microdados. RAIS, PNAD, INEP, Brasscom e Exame são referências da matriz, não bases importadas neste pacote. O CAGED disponível não corresponde ao ano inteiro nem ao mercado atual de 2026.

## 2 Perguntas P1 a P4 para o Novo CAGED

### P1 Quais faixas salariais aparecem nas admissões de TI em Pernambuco, Nordeste e Brasil?

**Universo:** Admissões (saldo=1), salário válido, ocupações de TI do recorte e geografia selecionada.

**Métricas:** p10, p50 e p90 do salário real; número de salários válidos por cargo, área e região.

**Visualização:** Faixa horizontal p10-p90 com marcador de mediana, por cargo ou área.

**Limite de interpretação:** Salário de admissão não é salário júnior. Percentis não são mínimo/máximo nem intervalo de confiança.

### P2 Como se distribuem admissões e desligamentos de TI no primeiro trimestre de 2025?

**Universo:** Todas as movimentações de TI, inclusive registros com salário sinalizado.

**Métricas:** Contagens de admissões e desligamentos; diferença entre as contagens dos arquivos MOV, por mês e região.

**Visualização:** Barras agrupadas por área e mês; linha mensal quando a dimensão temporal for o foco.

**Limite de interpretação:** A diferença MOV não é o saldo oficial final ajustado. Três meses não permitem inferir sazonalidade ou tendência longa.

### P3 Como as distribuições salariais agregadas de admissão e desligamento diferem no mesmo recorte?

**Universo:** Admissões e desligamentos com salário válido, estratificados pelo mesmo cargo, geografia e competência.

**Métricas:** p10/p50/p90 por movimento e diferença de medianas, somente quando ambos os grupos têm n>=30.

**Visualização:** Faixas lado a lado ou boxplots com escala compartilhada.

**Limite de interpretação:** São grupos distintos. A diferença não mede aumento salarial, promoção ou evolução da mesma pessoa.

### P4 Que relações aparecem entre salário de admissão, escolaridade, idade, jornada e ocupação?

**Universo:** Admissões com salário válido; idade/jornada válidas nas análises que usam esses campos.

**Métricas:** Distribuições por escolaridade; correlações de Spearman para idade/jornada; diferenças dentro de cargo e UF.

**Visualização:** Boxplots por escolaridade e dispersão com transparência; agrupamentos exploratórios se justificados.

**Limite de interpretação:** Idade não representa experiência ou senioridade. Escolaridade é categórica; associações não demonstram causalidade.

## 3 Perguntas P5 a P8 para o State of Data Brazil

### P5 Quais perfis de formação, vínculo e trabalho aparecem entre iniciantes na área de dados?

**Universo:** Residentes no Brasil; recortes separados de júnior declarado, estágio e experiência em dados de até dois anos.

**Métricas:** Contagens e proporções por perfil; total elegível, respondido e ausente em cada comparação.

**Visualização:** Barras horizontais e barras 100% empilhadas com poucas categorias.

**Limite de interpretação:** Início em dados não significa início em toda a carreira. Esses critérios não devem ser fundidos como equivalentes.

### P6 Como as faixas salariais declaradas se distribuem por cargo, senioridade e modelo de trabalho?

**Universo:** Residentes no Brasil com faixa salarial e categoria de comparação respondidas.

**Métricas:** Proporção de respostas em cada faixa salarial ordenada, por categoria; denominador e faltantes.

**Visualização:** Barras empilhadas ordenadas ou mapa de calor de proporções com rótulos.

**Limite de interpretação:** Não calcular salário exato ou média usando ponto médio. A faixa superior é aberta; não misturar com salários administrativos.

### P7 Quais tecnologias são declaradas pelos diferentes perfis da área de dados?

**Universo:** Residentes no Brasil que responderam ao grupo de tecnologias, estratificados por perfil ou área.

**Métricas:** Percentual de usuários de cada tecnologia entre respondentes elegíveis que responderam ao item/grupo.

**Visualização:** Barras horizontais por tecnologia; pequenos múltiplos para comparar perfis.

**Limite de interpretação:** Múltiplas escolhas podem somar mais de 100%. Ausência não é resposta negativa; opções 'nenhuma' não são tecnologias.

### P8 Que características se associam à busca ativa por emprego declarada na pesquisa?

**Universo:** Residentes no Brasil com resposta válida ao item planos_mudar_emprego_6m.

**Métricas:** Proporção de busca ativa, distribuição das classes e avaliação de classificadores contra uma referência simples.

**Visualização:** Barras de composição e, na etapa 05, matriz de confusão, ROC e precision-recall.

**Limite de interpretação:** O alvo é intenção declarada contemporânea, não desligamento futuro. A pergunta do alvo e suas cópias não entram como preditores.

## 4 Perguntas P9 a P12 para necessidades e intenções

### P9 Como os participantes avaliam o acesso à informação e quais dificuldades relatam?

**Universo:** 35 respostas do questionário próprio; cada item usa seu total válido.

**Métricas:** Distribuição das notas 1 a 5 e contagem/proporção das dificuldades; informar denominadores.

**Visualização:** Barras ordenadas para notas e barras horizontais para dificuldades.

**Limite de interpretação:** As âncoras da escala não estão no XLSX. Não chamar nota alta de facilidade maior antes de confirmar o formulário; não generalizar para todo o mercado.

### P10 Que informações os participantes priorizam e que intenção de uso da ferramenta declaram?

**Universo:** Q08: participantes com seleção reconhecida. Q07: somente respostas Sim/Não válidas.

**Métricas:** Pessoas que selecionaram cada opção / pessoas que responderam Q08; proporção de Sim em Q07 e total de respostas fora do domínio.

**Visualização:** Barras horizontais de prioridades; barra de composição para intenção válida.

**Limite de interpretação:** Seleções podem somar mais de 100%. Q07 tem três respostas fora do domínio. Intenção declarada em pergunta sobre a solução não comprova adoção ou desejabilidade validada.

### P11 Como a expectativa salarial declarada varia com a experiência informada em TI?

**Universo:** Expectativas não sinalizadas e experiência exata para relações quantitativas; intervalos são analisados separadamente.

**Métricas:** Mediana e quartis de expectativa; cobertura de experiência exata e intervalos; associação exploratória somente com n suficiente.

**Visualização:** Distribuição de expectativas; dispersão apenas em análise interna restrita, agregação em faixas na versão pública.

**Limite de interpretação:** R$5 é sinalizado, não corrigido para R$5.000. Sete a oito meses não viram 7,5. Sem cargo e UF comparáveis, e com coleta em 2026, não medir diferença individual contra CAGED de 2025.

### P12 Quantos participantes declaram buscar mudança e quantos cogitaram sair ou mudar de área?

**Universo:** Respostas válidas de Q10 e Q11, com denominadores separados.

**Métricas:** Contagens e proporções de Sim/Não por item; cobertura e respostas inválidas.

**Visualização:** Barras de composição por pergunta, sem concatenar os dois alvos.

**Limite de interpretação:** Q10 abrange emprego, área ou regime; não é o mesmo alvo do State of Data. Cogitar desistir não comprova saída; não treinar classificador com apenas 35 respostas.

## 5 Definições para assegurar comparações consistentes

| Métrica | Definição e regra |
| --- | --- |
| Faixa salarial real | p10/p50/p90 dos salários mensais válidos. p50 é a mediana; p10/p90 não são extremos nem confiança estatística. |
| Correção monetária | salario_real = salario_nominal × IPCA(mar/2025) / IPCA(competência). Unidade: reais por mês a preços de mar/2025. |
| Volume e diferença MOV | Admissões = contagem de saldo=1; desligamentos = contagem de saldo=-1. Diferença MOV = admissões - desligamentos no arquivo selecionado. |
| Participação em uma categoria | Respostas da categoria / respostas válidas do item no universo selecionado. Mostrar denominador e quantidade ausente. |
| Tecnologia declarada | Respostas True / (True + False) do item entre elegíveis. Não transformar ausente em False; itens de múltipla escolha podem exceder 100% em conjunto. |
| Correlação exploratória | Spearman para variáveis quantitativas observadas. Não atribuir ordem numérica arbitrária a UF, cargo ou escolaridade. |
| Dados insuficientes | Comparações estatísticas: n>=30 por grupo, regra operacional de estabilidade, não garantia de representatividade. Pesquisa G12: descrever o total e não fazer inferência de subgrupos pequenos. |

### Elegibilidade e qualidade

O pacote sinaliza 690 salários nominais fora do intervalo plausível de R$300 a R$200.000 ou inválidos. Eles permanecem nos dados e nas contagens de movimentações, mas não compõem as estatísticas salariais. Usar idade_valida e horas_validas quando essas variáveis forem analisadas.

No State of Data foram retiradas duas linhas exatamente repetidas. As linhas iguais do CAGED foram preservadas porque podem representar eventos distintos. Valores ausentes e respostas não aplicáveis serão informados com denominadores específicos; não haverá imputação automática na análise descritiva.

No G12 nenhuma linha foi removida. Q07 tem três respostas fora de Sim/Não, mantidas no original e excluídas da proporção válida. Uma expectativa salarial requer revisão. Um intervalo de experiência não vira valor exato. As âncoras de Q05 precisam ser confirmadas.

### Limites das fontes

CAGEDMOV cobre o emprego formal e não identifica pessoas, tempo de vínculo, senioridade ou habilidades. Não inclui neste pacote os ajustes FOR/EXC. A pesquisa é voluntária, autodeclarada e específica da área de dados. Faixas abertas de salário não serão convertidas em remuneração pontual. Três meses não sustentam previsão de longo prazo.

## 6 Objetivos visuais e princípios de percepção

| Pergunta e gráfico | Objetivo da comunicação | Justificativa visual |
| --- | --- | --- |
| P1: Faixa horizontal p10-p90 com marcador de mediana, por cargo ou área. | Comparar remuneração de contratação e dispersão entre ocupações e regiões. | Posição em um eixo comum facilita comparação; a faixa mostra dispersão sem reduzir o grupo a uma média. |
| P2: Barras agrupadas por área e mês; linha mensal quando a dimensão temporal for o foco. | Mostrar o volume e a composição dos movimentos formais no trimestre. | Comprimentos com origem em zero permitem comparar volumes; meses em ordem preservam a leitura temporal. |
| P3: Faixas lado a lado ou boxplots com escala compartilhada. | Mostrar sobreposição e diferenças entre grupos, sem sugerir evolução individual. | Alinhamento e escala comum mostram diferenças e sobreposição entre distribuições. |
| P4: Boxplots por escolaridade e dispersão com transparência; agrupamentos exploratórios se justificados. | Explorar associações e variação salarial dentro de recortes comparáveis. | Boxplots comunicam centro e variação; dispersão revela forma, concentração e observações extremas. |
| P5: Barras horizontais e barras 100% empilhadas com poucas categorias. | Caracterizar perfis de entrada na área de dados sem confundir critérios de experiência. | Barras permitem comparação precisa; proporções distinguem composição de diferença no tamanho dos grupos. |
| P6: Barras empilhadas ordenadas ou mapa de calor de proporções com rótulos. | Comparar a composição das faixas de salário, sem fabricar valores exatos. | Ordem das faixas preserva a interpretação ordinal; valores e legenda reduzem a dependência da cor. |
| P7: Barras horizontais por tecnologia; pequenos múltiplos para comparar perfis. | Mostrar tecnologias declaradas por perfil e a cobertura de cada pergunta. | Comprimento é mais preciso que área para comparar frequência; pequenos múltiplos preservam a mesma escala. |
| P8: Barras de composição e, na etapa 05, matriz de confusão, ROC e precision-recall. | Comunicar os erros e os limites da classificação de busca ativa declarada. | A matriz localiza os erros de cada classe; curvas mostram o efeito do limiar e da composição das classes. |

### Apresentação no Radar

Priorizar visão geral de Pernambuco, ampliar para Nordeste e Brasil e permitir detalhe por cargo/área e período. Separar as páginas de emprego formal e perfis da área de dados. Usar a identidade visual já definida em app/theme.py: contraste, uma cor de destaque, rótulos diretos e escala comum nas comparações.

Toda visualização informará fonte, período, unidade, universo, n válido e exclusões relevantes. Barras partem de zero; eixos não serão truncados de forma enganosa. Cores não serão o único meio de distinguir séries. Recortes vazios ou insuficientes terão mensagem explícita.

## 7 Objetivos visuais, integração e privacidade

| Pergunta e gráfico | Objetivo da comunicação | Justificativa visual |
| --- | --- | --- |
| P9: Barras ordenadas para notas e barras horizontais para dificuldades. | Identificar dificuldades de informação na amostra própria para orientar a solução. | Ordem preserva a escala ordinal; comprimentos permitem comparar categorias sem atribuir distância psicológica igual às notas. |
| P10: Barras horizontais de prioridades; barra de composição para intenção válida. | Priorizar conteúdo do painel e distinguir intenção de uso de adoção real. | Comprimento mostra frequência das prioridades; composição usa denominador específico da pergunta, não o número de opções selecionadas. |
| P11: Distribuição de expectativas; dispersão apenas em análise interna restrita, agregação em faixas na versão pública. | Caracterizar expectativas da amostra, preservando limites e privacidade. | Distribuição mostra variação sem inventar salário recebido; faixas agregadas reduzem a exposição de perfis individuais na amostra pequena. |
| P12: Barras de composição por pergunta, sem concatenar os dois alvos. | Descrever intenções distintas de mudança, sem apresentar causa ou previsão. | Perguntas separadas mantêm seus significados e permitem ler composição sem sugerir trajetória longitudinal ou causa. |

### Integração sem mistura de populações

O dashboard terá seções separadas de emprego formal, perfis em dados e pesquisa do grupo. Aproximar temas, não juntar pessoas. Expectativa salarial de 2026, salário formal de 2025 e faixas da pesquisa nacional não são uma única variável. Q10 do G12 e busca ativa do State of Data têm significados diferentes.

### Publicação responsável

Originais e respostas individuais G12 ficam locais e ignorados pelo Git. IDs novos são pseudônimos de linha, não garantia de anonimização. O horário exato da coleta não entra nas tabelas analíticas. Consentimento para divulgação não está documentado no XLSX e deve ser confirmado antes de publicar.

Evitar cruzamentos raros, pontos individuais e respostas brutas na versão pública. Agregar e avaliar risco de reidentificação; suprimir células com menos de cinco respostas e, quando necessário, células complementares. Essa regra não substitui revisão de privacidade ou autorização dos participantes.

## 8 Protocolos previstos para as etapas 04 e 05

### Regressão para salário de admissão

Universo: admissões de TI com salario_valido=True. Alvo: salario_real. Entradas candidatas: cargo/CBO, UF, escolaridade, idade e jornada. Começar com um modelo linear simples e comparar com uma referência que prevê a mediana do treino. Relacionar diferenças por cargo e UF antes de interpretar coeficientes.

Treino inicial: janeiro e fevereiro de 2025. Avaliação final: março de 2025, reservado antes do ajuste. Escalas, imputação e codificação de categorias serão ajustadas apenas no treino. Não usar salario_nominal, salario_fixo_declarado, faixa_salario_real, escalas do alvo ou registros de origem como preditores.

Entregar MAE/RMSE, observados versus previstos, dispersão com tendência e resíduos versus previsão. Verificar desempenho por UF/área quando houver registros suficientes. Os modelos representam relações no recorte e não acompanham a evolução da mesma pessoa.

### Classificação de busca ativa por emprego

Universo: residentes no Brasil com planos_mudar_emprego_6m respondido. Há 4.734 respostas elegíveis: 1.630 em busca ativa e 3.104 sem busca ativa. Estes totais caracterizam o alvo disponível; o desempenho do modelo ainda será medido.

| Classe | Regra baseada na resposta original |
| --- | --- |
| 1 - Busca ativa | Estou em busca de oportunidades dentro ou fora do Brasil; ou estou em busca de oportunidades, mas apenas fora do Brasil. |
| 0 - Sem busca ativa | Não estou buscando, mas me considero aberto a outras oportunidades; ou não estou buscando e não pretendo mudar de emprego nos próximos 6 meses. |
| Ausente | Excluir da tarefa supervisionada; não converter em classe 0. |

Entradas iniciais: senioridade declarada, formação, vínculo, modelo de trabalho e experiência em dados. Excluir a pergunta-alvo e cópias no arquivo completo; na primeira versão, também excluir entrevistas recentes, oportunidades buscadas e tempo de busca, que podem aproximar diretamente a resposta.

Separar treino/teste estratificados, 80%/20%, com semente fixa 12. Comparar referência de classe majoritária, regressão logística e árvore simples. Ajustar pré-processamento e limiar com o treino, sem consultar o teste. Entregar matriz de confusão, acurácia, precisão, recall, F1, ROC e precision-recall; explicitar a classe positiva e o limiar.

## 9 Rastreabilidade da etapa 01 e próximos passos

### Critérios da etapa 01

| Critério | Evidência neste plano |
| --- | --- |
| Dados que serão utilizados | Fontes, recortes e unidades na seção de escopo e no catálogo; registro distingue dados importados e referências. |
| Perguntas de análise | P1 a P12, com universo, colunas e limites. Matriz CSV acompanha o documento. |
| Métricas previstas | Quantis, contagens, proporções, relações e avaliação definidos nas perguntas, regras e protocolos. |
| Objetivos da comunicação visual | Objetivo explícito por pergunta nas duas seções de visualizações e na matriz CSV. |
| Justificativa dos gráficos | Posição, comprimento, distribuição, ordem, contraste, escala e privacidade fundamentam as escolhas. |

### Sequência de execução

Concluir o plano de preparação (02). Executar P1 a P12 na exploração (03), verificando domínio de Q07, expectativa sinalizada, escala Q05 e protocolo de recrutamento. Desenvolver regressão (04) e classificação (05) com as bases adequadas, não com a pequena amostra G12. Implementar dashboard/publicação (06), validar (07) e documentar (08).

A elaboração deste plano não conclui a análise exploratória, modelos ou validação com usuários. Os artefatos do ciclo anterior continuam preservados na raiz do projeto e serão tratados como histórico do recorte anterior.

### Referências e procedência

**Critérios:** Entregáveis 5ºP - Projeto 2026.1-2, coluna CC Análise e Visualização de Dados, copiado para 00_referencias/criterios_avd_cc.pdf.

**MTE:** [Microdados RAIS e CAGED](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged). Originais e layout em datasets/brutos.

**Data Hackers:** [State of Data Brazil 2024-2025](https://www.kaggle.com/datasets/datahackers/state-of-data-brazil-20242025); arquivo obtido do espelho público da comunidade, registrado no manifesto.

**IBGE:** [IPCA SIDRA, tabela 1737 e variável 2266](https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/202501-202503); [API de Localidades](https://servicodados.ibge.gov.br/api/v1/localidades/municipios) para municípios.

**Reprodução:** datasets/fontes_manifesto.json, auxiliares/dicionario_dados.csv, qualidade/relatorio_qualidade.json e qualidade/validacao_exports.json. Os arquivos brutos têm hashes SHA-256 registrados.

**Grupo 12:** questionário e matriz XLSX fornecidos pelo grupo. Manifesto próprio, mapa de perguntas, relatório de qualidade e script prepare_grupo12.py preservam sua procedência. A fase 01 atende documentalmente aos cinco critérios; isso não representa aprovação da professora ou conclusão das fases seguintes.
