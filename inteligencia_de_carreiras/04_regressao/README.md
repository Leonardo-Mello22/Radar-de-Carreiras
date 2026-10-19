# Regressão Salarial

Etapa 04 do Radar de Carreira em TI: representar tendências e limites do salário
real de admissão usando modelos lineares simples, com avaliação temporal.
Somente Novo CAGED MOV de janeiro a março de 2025; sem pesquisa G12 ou State of Data.

## Entrega

- [Análise completa em HTML](resultados/regressao_salarial.html), com gráficos e interpretações.
- [Notebook executado](resultados/regressao_salarial_executada.ipynb).
- [Notebook de código, sem saídas](regressao_salarial.ipynb).
- [Síntese dos achados calculados](sintese_achados.md).
- [Protocolo e decisões metodológicas](metodologia.md).
- [Conferência dos critérios](verificacao_fase04.md).
- [Registro de execução e hashes](registro_execucao.json).

## Organização

```text
04_regressao/
  README.md                      índice e reprodução
  metodologia.md                 universo, modelos, métricas e limites
  regressao_salarial.ipynb        notebook sem saídas
  regressao.py                   regras, modelos, gráficos e interpretação
  executar_regressao.py           execução real do notebook e exportação
  requirements.txt               versões da execução
  sintese_achados.md              resultados gerados, não valores digitados
  verificacao_fase04.md           critérios e evidências
  registro_execucao.json          versões e integridade dos produtos
  tests/                         testes de regras e dos artefatos executados
  resultados/
    regressao_salarial.html
    regressao_salarial_executada.ipynb
    auditoria_modelagem.json
    graficos/                    seis figuras, com fonte e universo
    tabelas/                     CSV completos e coeficientes
  resultados_locais/             ignorada pelo Git: previsões por evento e caches
```

## Método Resumido

O conjunto tem 60.862 admissões com salário válido. Janeiro e fevereiro, com
41.037 eventos, formam o treino final; março, com 19.825, é o teste reservado.
A escolha usa MAE em uma validação interna anterior: janeiro para ajuste e
fevereiro para avaliação. Depois, os três modelos são reajustados em janeiro-fevereiro
e avaliados no mesmo teste, sem trocar o escolhido.

Comparação: mediana do treino, regressão linear por idade e regressão linear
múltipla com Ridge de penalização fixa. Entradas da múltipla: idade, horas
contratuais, CBO, UF e escolaridade. Pré-processamento é aprendido somente no treino.
Variáveis salariais derivadas, IDs e variáveis de origem não entram como preditores.

O notebook mostra dispersão e tendência, observado versus previsto, resíduos,
MAE/RMSE/R², erros por recorte, calibração descritiva e sensibilidade à cauda.
Os CSV completos ficam em `resultados/tabelas/`; tabelas extensas são abreviadas
na leitura do notebook, com aviso explícito.

## Reproduzir

Na raiz do repositório, após a preparação completa da etapa 02:

```powershell
python -m pip install -r inteligencia_de_carreiras/04_regressao/requirements.txt
python inteligencia_de_carreiras/04_regressao/executar_regressao.py
python -m unittest discover -s inteligencia_de_carreiras/04_regressao/tests -v
```

O runner verifica o SHA-256 do CAGED contra a preparação, cria um kernel local,
executa todas as células e exporta o HTML com imagens embutidas. Nenhum servidor
é necessário para ler o HTML. O pacote tratado precisa estar disponível localmente;
os dados grandes não são distribuídos pelo Git. O notebook também pode ser executado
no Jupyter/VS Code a partir da raiz do repositório ou desta pasta.

`resultados/` contém apenas tabelas e gráficos agregados da fonte pública;
o notebook executado é versionável. O extrato de previsões por evento e o kernel
ficam em `resultados_locais/`, fora do Git. Não há publicação automática, commit
ou alteração do dashboard pelo runner.

## Limites

Salários mensais reais em R$ de março de 2025, não salários atuais de 2026.
Uma linha é um evento, não uma pessoa. Idade não é experiência; admissão não é
senioridade júnior. As relações são observacionais, não causais. Apenas um mês de
teste não permite avaliar sazonalidade ou prever a carreira de alguém.
Todos os salários válidos entram nas métricas; cortes visuais não excluem eventos.
Não há intervalos individuais, p-valores ou garantia de independência dos eventos.
A etapa 05 continua separada e pendente.
