# Plano de preparação dos dados

Etapa 02. Versão 1.0. 14 de outubro de 2026.

## 1. Preparação dos dados

Etapa 02 - Plano, justificativas e execução

**Radar de Carreira em TI - Grupo 12 - CESAR School**
Versão 1.0 - 14 de outubro de 2026

**Objetivo:** tornar as fontes adequadas às perguntas P1-P12 da fase 01, mantendo origem, unidade de observação, significado das variáveis e limitações. A etapa entrega o plano e um pipeline executado, não resultados de exploração ou modelos.

| Fonte e formato bruto | Recorte tratado | Uso e justificativa |
| --- | --- | --- |
| Novo CAGED: três .7z com texto UTF-8 separado por ;. Layout oficial XLSX. | Jan-mar/2025: 118.564 movimentos, 62 campos; PE e Nordeste como subconjuntos. | Emprego formal e salário mensal. Famílias CBO delimitam ocupações do Radar. |
| State of Data: ZIP com CSV, 403 campos originais. | 5.215 respostas; base de carreiras com 51 campos. | Perfis em dados, faixas de salário e busca declarada; pesquisa voluntária. |
| Grupo 12: questionário XLSX e matriz XLSX. | 35 respostas/12 perguntas; 21 referências e hipóteses. | Necessidades e intenções; matriz é contexto, não amostra de trabalhadores. |
| IBGE: municípios e IPCA em JSON. | 5.571 municípios; três índices/fatores de IPCA. | Tradução territorial e salários a preços de mar/2025. |

### Saídas e procedência

CSV UTF-8 com BOM, vírgula, ponto decimal e ausências vazias; Parquet preserva tipos. Nomes de colunas únicos em snake_case, texto NFC e espaços normalizados. Códigos não são números de medida. Nove arquivos brutos têm SHA-256 verificado; versões e produtos constam no relatório de execução.

Os estudos continuam separados. RAIS, PNAD, INEP, Brasscom, Exame e similares são referências da matriz, não bases importadas. A fase 02 não acrescenta dados simulados nem preenche pesquisas ainda não realizadas.

## 2. Emprego formal: Novo CAGED

Filtros, categorias e transformações para P1-P4

| Variáveis | Decisão aplicada | Justificativa |
| --- | --- | --- |
| CBO e área de TI | Famílias 1236/1425/2122/2123/2124/3171/3172; 27 CBOs. Código de seis dígitos, descrição oficial e área analítica. | Escopo explícito, preservando zeros. Inclui automação; não cobre toda carreira possível de TI. |
| Movimento e competência | saldo 1/-1; calendário derivado; conservar mês do movimento e da declaração. | Contar eventos, não pessoas ou vagas. MOV sem FOR/EXC não é saldo final ajustado. |
| UF e município | Ligar código CAGED de seis dígitos à chave IBGE única de sete; recortes PE/NE/Brasil. | Evitar duplicação por join e garantir filtros geográficos legíveis. |
| Salário mensal | Número brasileiro; validade nominal [300,200000]; sinalizar, não remover. Não multiplicar o campo salario por horas/dias. | A unidade do componente fixo não altera o salário mensal do layout; controles não apagam movimentos. |
| Salário real e faixas | nominal × IPCA(mar/2025)/IPCA(mês). Faixas [0,2000), [2000,4000), [4000,6000), [6000,10000), [10000,15000), [15000,+inf). | Comparar poder de compra; limites claros, sem converter faixa em ponto exato. |
| Idade e jornada | Idade válida [14,90]; jornada [1,48]. Originais mantidos, sinalizados excluídos apenas de relações/escalas que os usam. | Limites operacionais de plausibilidade, não conclusão legal; idade não é experiência. |
| Escolaridade e vínculo | Preservar código e texto oficiais; agrupar escolaridade; booleanos anuláveis para indicadores. | Categorias não viram ordem numérica arbitrária; primeiro emprego não equivale a júnior. |

Leitura em lotes de 200.000 linhas limita memória. Foram examinadas 13.530.056 linhas brutas. Nenhuma movimentação selecionada é removida por salário sinalizado. As 1.386 linhas iguais sem ID ficam: a fonte não identifica pessoas e podem ser eventos distintos.

## 3. Perfis: State of Data

Preparação conservadora para P5-P8

| Variáveis | Decisão aplicada | Justificativa |
| --- | --- | --- |
| Registro e schema | 5.217 respostas originais; remover só duas linhas completamente iguais; IDs preservam linha de origem. | Deduplicação explícita, sem apagar respostas apenas parecidas; ID não liga pessoas a outras fontes. |
| Gestão, cargo e área | Indicador de gestor como booleano anulável. Gestor declarado sem cargo técnico recebe Gestao. | Correção do erro texto/booleano: 1.045 gestores não devem cair em outra área por falha de tipo. |
| Senioridade e experiência | Nível apenas declarado. Até dois anos usa experiência em dados; experiência anterior em TI fica separada. | Sem inventar júnior e sem confundir entrada em dados com início de toda a carreira. |
| Faixa de salário | Guardar texto, limites e exclusividade; faixa acima de R$40.001 permanece aberta. | Não criar salário exato, média por ponto médio ou comparação direta com remuneração administrativa. |
| Formação, vínculo e trabalho | Categorias por mapeamento explícito, conservando declarações originais na base completa. | Reduzir complexidade visual sem esconder distinções; não informado não é uma categoria de emprego. |
| Tecnologias e residência | Tecnologias anuláveis; tabela longa só com seleções. Brasil pelo item de residência; regiões por UF. | Nulo não é False. Denominador vem de elegibilidade do item; recortes são subconjuntos. |
| Busca ativa e proxies | Manter quatro respostas originais e alvo planejado separado; excluir resposta-alvo e proxies próximos no modelo. | Ausente não vira classe negativa; intenção não mede saída futura. |

Os 403 campos originais geram 405 colunas com ID/fonte; a versão de carreiras tem 51. Nulos podem decorrer de ramificações, como perguntas não feitas a gestores ou desempregados. Não aplicar complete-case global: avaliar elegibilidade por pergunta e evitar excluir sistematicamente perfis.

## 4. Pesquisa própria e matriz

Tratamento de Q01-Q12 e referências para P9-P12

| Item | Tratamento aplicado | Justificativa e limite |
| --- | --- | --- |
| Schema e coleta | 35 respostas; reconhecer número da pergunta, inclusive Q02 no fim. Descartar coluna vazia. Guardar mês, não horário exato, no analítico. | Ordem da exportação não altera semântica. IDs de linha não garantem anonimização. |
| Q05: nota 1-5 | Validar domínio ordinal e preservar notas; não deduzir âncoras/direção. | XLSX não informa o sentido dos extremos; confirmar formulário antes de medir satisfação. |
| Q07: Sim/Não | Três respostas fora do domínio: original preservado, booleano ausente e flag. Denominador válido = 32. | Não adivinhar intenção nem deslocar respostas para outra pergunta. |
| Q08: prioridades | Reconhecer sete textos completos; de uma a três seleções. 101 linhas derivadas, não 101 pessoas. | Vírgulas internas não separam opções. Percentual usa participantes que responderam, não total de seleções. |
| Q09: expectativa | Inteiro mensal; revisão fora de [300,200000] ou não parseável. R$5 mantido e sinalizado. | Não corrigir para milhares nem confundir expectativa com salário recebido; analisar sensibilidade. |
| Q12: experiência | Anos/meses inequívocos convertidos. Intervalo 7-8 mantém limites e exato ausente; zero válido. | Não transformar intervalo em média ou inventar experiência. |
| Q10/Q11 e matriz | Sim/Não por item; matriz mantém 21 achados e 10 links, com CSD declarado e alertas. | Emprego/área/regime não equivale ao alvo State of Data. Referência importada não é evidência verificada. |

Curso, momento e período permanecem declarados; desperiodizado não vira período zero. O grupo tem tabelas separadas de respostas (35), respostas longas (420) e prioridades (101). Sem cargo padronizado/UF e com coleta em 2026, não medir diferença salarial individual contra o CAGED de 2025.

## 5. Nulos, escalas e uso analítico

Elegibilidade e proteção contra vazamento

| Uso | Regra | Justificativa |
| --- | --- | --- |
| Descrição | Sem imputar média/zero/Não; informar total, válidos, ausentes e exclusões por variável. | Ausência, não aplicável e zero são diferentes; denominador não pode mudar silenciosamente. |
| Salários CAGED | Usar salario_valido; conservar todos os movimentos nos volumes. Quantis por grupo só com n>=30. | Evitar estatística salarial instável sem apagar contratações; n>=30 não comprova representatividade. |
| Z-score e min-max | Ajustes do pacote em valores válidos: (x-média)/desvio populacional e (x-min)/(max-min). log1p no salário real. | Escalas exploratórias são separadas dos reais; inválidos permanecem ausentes na tabela de features. |
| Regressão prevista | Jan/fev treino; março teste. Ajustar codificação/escalas/imputação só no treino; excluir salário nominal, faixas/escalas do alvo e IDs. | Evitar vazamento e medir relação salarial num período reservado, não trajetória da pessoa. |
| Classificação prevista | State of Data Brasil com alvo respondido; split 80/20 estratificado, semente 12. Excluir alvo, cópias e proxies; não adicionar as 35 respostas G12. | Perguntas e públicos diferentes não aumentam artificialmente o treino; modelo ainda não executado. |
| Publicação G12 | Originais e respostas individuais fora do Git. Revisar consentimento e agregados, células raras e supressão complementar. | Pseudônimo não elimina reidentificação; agregação pequena exige revisão antes de divulgação. |

### Pendências de confirmação

Permanecem para confirmação: âncoras Q05, três respostas Q07 fora do domínio, expectativa sinalizada, protocolo de recrutamento e autorização de divulgação. A preparação os registra e permite análises restritas; não os resolve por inferência automática.

## 6. Pipeline reproduzível

Da fonte verificada ao pacote validado

| Passo | Execução e saída |
| --- | --- |
| 1. Procedência | Verificar nove SHA-256 antes de transformar; origem pública e XLSX próprios têm manifestos separados. |
| 2. Fontes públicas | prepare_datasets.py: schema, survey, CAGED em lotes, dimensões, recortes, agregados e escalas. |
| 3. Pesquisa própria | prepare_grupo12.py: respostas, tabela longa, prioridades, matriz, dicionário e alertas. |
| 4. Validação | validate_package.py: CSV/Parquet em valores, fontes, contagens, relações, deflação, categorias e domínios. |
| 5. Testes e evidência | unittest; execucao_preparacao.json com ambiente, código, fontes, etapas e SHA-256 dos produtos. |

### Executar na raiz do repositório

```powershell
python -m pip install -r `
  inteligencia_de_carreiras/02_preparacao_dados/requirements_reproducao.txt
```

Executar o pipeline completo com os originais locais:

```powershell
python inteligencia_de_carreiras/datasets/scripts/run_preparation.py
```

Para conferir somente o pacote existente, acrescentar --mode validate. O pipeline não baixa dados automaticamente. Em outra máquina, reconstruir o pacote público com download_sources.py e obter os XLSX do grupo por canal autorizado; conferir/registrar os manifestos antes de processar.

### Cache e recursos

Cache temporário fora do OneDrive por padrão; --temporary permite escolher outra pasta. Chave inclui o código de transformação e SHA-256 do arquivo CAGED, layout, municípios e IPCA. Mudança de fonte ou regra invalida o reaproveitamento. Temporários não são exports finais nem entram na validação de CSV.

Reservar alguns GB em disco para os textos descompactados; memória é limitada pela leitura em lotes, mas tabelas finais e exports ainda consomem recursos. Sem acesso à internet, os nove brutos já disponíveis permitem reprodução offline. Fontes privadas não são distribuídas pelo Git.

## 7. Controles e resultados da preparação

Evidência de execução, não de análise exploratória

| Controle | Resultado do pacote revisado |
| --- | --- |
| CAGED: população | 13.530.056 linhas verificadas; 118.564 movimentos de TI; PE 2.305; Nordeste 10.704. |
| CAGED: salário e cobertura | 690 salários sinalizados; 117.874 válidos. Sem CBO/município sem tradução; 395 jornadas sinalizadas. |
| CAGED: duplicatas e agregado | 1.386 linhas iguais sem ID preservadas; 1.227 grupos conciliados com volumes/quantis e bloqueio n<30. |
| State of Data | 5.217 originais; 5.215 após duas duplicatas exatas; Brasil 5.076. 1.399 senioridades ausentes mantidas. |
| Correção de gestão | 1.045 gestores declarados; 1.045 enquadrados em Gestao quando cargo técnico não respondido. Tipos conciliados com a origem. |
| Grupo 12 | 35 respostas/12 perguntas; 420 respostas longas; 101 prioridades; três Q07 fora de domínio; uma expectativa e um intervalo sinalizados. |
| Matriz de pesquisa | 21 itens e 10 links preservados. Certezas, suposições e dúvidas são declarações, não verificação externa. |
| Rastreabilidade por coluna | 582 linhas de decisões na matriz de pré-processamento, incluindo os campos da base completa e dimensões. |

### Ambiente e execução

Python 3.12.14; pandas 3.0.1, numpy 2.3.5, pyarrow 26.0.0, py7zr 1.1.4, openpyxl 3.1.5. A execução registrada tem modo **full**, com fontes e produtos conferidos. O relatório JSON preserva tempos, versões e hashes sem conteúdo das respostas individuais.

A validação técnica passou com alertas semânticos documentados. Validar estrutura não comprova representatividade, veracidade de relatos ou consentimento. Exploração dos dados e avaliação de regressão/classificação serão executadas nas fases seguintes.

## 8. Critérios de aceite e referências

Rastreabilidade da entrega CC02

| Critério solicitado | Evidência entregue |
| --- | --- |
| Fontes abertas/próprias e formatos | Escopo, formatos e unidades no plano; catálogo, registro e dois manifestos. Sem dados simulados. |
| Limpeza e normalização | Nomes/tipos/texto, tradução de códigos, domínio, duplicatas, nulos e limites documentados e implementados. |
| Transformações para análise | Recortes, deflação, faixas, categorias, tabelas longas, agregados e escalas com uso específico. |
| Justificativa por variável | Matriz CSV com dataset, coluna, tipo, nulos, regra, justificativa e relação com P1-P12. |
| Reprodução e revisão | Comando único, ambiente registrado, fontes por SHA-256, validação em valores e testes executados. |

### Referências

Critérios fornecidos pelo grupo: Entregáveis 5ºP - Projeto 2026.1-2, coluna CC Análise e Visualização de Dados. O plano da fase 01 define as perguntas; esta fase justifica como preparar suas variáveis.

[MTE: microdados Novo CAGED e layout](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged). [Data Hackers: State of Data Brazil 2024-2025](https://www.kaggle.com/datasets/datahackers/state-of-data-brazil-20242025). IBGE: IPCA SIDRA tabela 1737/variável 2266 e API de Localidades. URLs, datas e hashes no manifesto público.

Pesquisa e matriz G12: XLSX fornecidos pelo grupo, copiados intactos e registrados em manifesto próprio. Enunciados, hyperlinks e textos originais foram preservados.

### Situação da etapa

A etapa 02 está concluída documental e tecnicamente para este pacote, com alertas explícitos. Aprovação acadêmica depende da avaliação da professora. A etapa 03 começará a exploração P1-P12; revisões por confirmação de respostas devem gerar nova versão de fonte/manifesto, não sobrescrever silenciosamente o histórico.
