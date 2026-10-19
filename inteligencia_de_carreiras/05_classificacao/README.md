# Classificação de Busca Ativa

Etapa 05: avaliação visual de classificadores simples de busca ativa **declarada**
por emprego no State of Data Brazil 2024-2025. Não é previsão de saída futura,
ferramenta para avaliar candidatos ou sistema de monitoramento de empregados.

## Entrega

- [Análise completa em HTML](resultados/classificacao_busca_ativa.html).
- [Notebook executado, com gráficos e interpretações](resultados/classificacao_busca_ativa_executada.ipynb).
- [Notebook de código, sem saídas](classificacao_busca_ativa.ipynb).
- [Síntese dos achados calculados](sintese_achados.md).
- [Metodologia e prevenção de vazamento](metodologia.md).
- [Conferência da etapa 05](verificacao_fase05.md).
- [Registro de execução, versões e hashes](registro_execucao.json).

## Organização

```text
05_classificacao/
  README.md                           índice e reprodução
  metodologia.md                      alvo, modelos, métricas e limites
  classificacao_busca_ativa.ipynb       notebook sem saídas
  classificacao.py                     regras, treinamento, gráficos e interpretação
  executar_classificacao.py            execução real do notebook e exportação
  requirements.txt                    versões da execução
  sintese_achados.md                   achados gerados a partir das métricas
  verificacao_fase05.md                critérios e evidências
  registro_execucao.json               integridade do código, fonte e produtos
  tests/                              testes de regras e resultados executados
  resultados/
    classificacao_busca_ativa.html
    classificacao_busca_ativa_executada.ipynb
    auditoria_modelagem.json
    graficos/                         sete figuras
    tabelas/                          treze CSV agregados
  resultados_locais/                  IDs, probabilidades individuais e caches; fora do Git
```

## Método Resumido

Dos 5.076 residentes no Brasil, 4.734 têm o alvo respondido: 1.630 em busca ativa
e 3.104 sem busca ativa. As 342 respostas sem alvo são excluídas, nunca convertidas
em classe 0. Treino e teste estratificados, 80/20, semente 12: 3.787 e 947 respostas.

Comparação entre classe majoritária, regressão logística e árvore simples.
Seleção pela maior Average Precision média em cinco folds estratificados do
treino. Hiperparâmetros e limiar 0,5 fixos; o teste não decide modelo ou limiar.

Entradas: senioridade declarada, nível de ensino, vínculo agrupado, modelo de
trabalho declarado e faixa de experiência em dados. Categorias são aprendidas
somente no treino. Pergunta-alvo, cópias e perguntas que aproximam diretamente a
resposta são excluídas. Não há junção com CAGED ou pesquisa G12.

O notebook contém acurácia, precisão, recall, F1, matriz de confusão, ROC-AUC,
precision-recall/AP, efeito do limiar apenas no treino e calibração descritiva.
As interpretações explicitam o baixo recall observado e o viés de elegibilidade.
Resultados limitados são parte da análise; não foram ocultados nem corrigidos
reutilizando o teste. Tabelas longas são abreviadas na leitura, com aviso e CSV completo.

## Reproduzir

Na raiz do repositório, após a preparação completa da etapa 02:

```powershell
python -m pip install -r inteligencia_de_carreiras/05_classificacao/requirements.txt
python inteligencia_de_carreiras/05_classificacao/executar_classificacao.py
python -m unittest discover -s inteligencia_de_carreiras/05_classificacao/tests -v
```

O runner confere o SHA-256 do State of Data preparado, registra um kernel local,
executa todas as células e exporta o HTML com imagens embutidas. O HTML abre sem
servidor ou instalação do Jupyter. O dataset tratado precisa estar disponível
localmente, conforme as instruções da etapa 02; não é distribuído por este Git.
O notebook pode ser executado no Jupyter/VS Code a partir da raiz ou desta pasta.

## Dados e Uso Responsável

Gráficos, notebook executado, auditoria e tabelas de `resultados/` são agregados
da fonte pública. Probabilidades por participante, IDs e caches ficam apenas em
`resultados_locais/`, ignorada pelo Git. Não há publicação automática ou commit.

A amostra é voluntária, específica da área de dados e da coleta 2024-2025.
Há viés de elegibilidade: muitos desempregados/estudantes não têm esse item
respondido. Senioridade ausente pode decorrer de ramificação do formulário.
O teste pertence à mesma coleta, sem avaliação temporal ou externa.
O desempenho não valida o uso para decisões laborais individuais. O aplicativo
existente não foi alterado; integração e publicação pertencem à etapa 06.
