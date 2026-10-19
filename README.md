# 🧭 Radar de Carreira em TI

Projeto de análise e visualização de dados para apoiar a compreensão do mercado
de trabalho e das trajetórias em tecnologia, com foco inicial em **Pernambuco e
Nordeste**. Combina dados oficiais de emprego formal, pesquisa sobre carreiras
em dados e pesquisa própria do Grupo 12, mantendo cada fonte em seu contexto.

> **Projeto 5 · CESAR School · 2026.2 · Grupo 12** — Trilha de Análise e Visualização de Dados.
> O repositório preserva a aplicação do **Ciclo 1** e reúne, separadamente, as
> **oito etapas de inteligência de carreiras**, com dashboard AVD consolidado v1.1.

## Mapa do Repositório

| Área | Ponto de entrada | Escopo |
| --- | --- | --- |
| Aplicação existente do Ciclo 1 | [app/dashboard.py](app/dashboard.py) | Implementação original, com pipeline em `src/` e dados em `data/processed`; preservada |
| Inteligência de carreiras / AVD | [README da área](inteligencia_de_carreiras/README.md) | Dados, análise exploratória, modelos, dashboard e documentação das oito etapas |
| Documentação geral | [Índice de documentação](docs/README.md) | Navegação pela documentação atual e pelos registros originais do Ciclo 1 |

As aplicações têm entradas distintas. O dashboard AVD **não substitui nem altera**
o aplicativo existente, seu pipeline ou suas fontes. Ele reutiliza a identidade
visual existente, sem modificar sua implementação.

## Entregas de AVD

| Etapa | Conteúdo principal |
| --- | --- |
| [01. Plano de análise](inteligencia_de_carreiras/01_plano_de_analise/README.md) | 12 perguntas, métricas e justificativa das visualizações |
| [02. Preparação dos dados](inteligencia_de_carreiras/02_preparacao_dados/README.md) | Filtros, categorias, valores ausentes, normalização e pipeline reproduzível |
| [03. Análise exploratória](inteligencia_de_carreiras/03_analise_exploratoria/README.md) | Notebook executado, distribuições, relações, agrupamentos e interpretação |
| [04. Regressão](inteligencia_de_carreiras/04_regressao/README.md) | Salários do CAGED, referência de mediana, teste temporal e resíduos |
| [05. Classificação](inteligencia_de_carreiras/05_classificacao/README.md) | Busca ativa declarada no State of Data, treino/teste e avaliação dos classificadores |
| [06. Dashboard e publicação](inteligencia_de_carreiras/06_dashboard_e_publicacao/README.md) | Dashboard inicial, filtros e proposta de integração/publicação web |
| [07. Consolidação e validação](inteligencia_de_carreiras/07_consolidacao_e_validacao/README.md) | Dashboard v1.1, auditoria numérica e testes funcionais desktop/mobile |
| [08. Documentação final](inteligencia_de_carreiras/08_documentacao_final/README.md) | Decisões, histórico, insights, capturas, limitações e guia de entrega |

As oito etapas organizam os dez entregáveis de CC: a etapa 06 reúne dashboard
inicial e proposta de integração; a 07 reúne consolidação e versão quase final.
Consulte a [matriz de critérios](inteligencia_de_carreiras/00_referencias/matriz_criterios.csv),
a [documentação final em PDF](inteligencia_de_carreiras/08_documentacao_final/documentacao_final.pdf)
e o [guia de entrega](inteligencia_de_carreiras/08_documentacao_final/guia_entrega.md).

## Dados da Área de Inteligência

| Fonte | Recorte preparado | Unidade e cuidado principal |
| --- | --- | --- |
| Novo CAGED / MTE | Janeiro a março de 2025; 118.564 movimentações de TI no Brasil, sendo 2.305 em PE | Eventos de emprego formal, não pessoas; salários corrigidos pelo IPCA para março de 2025 |
| State of Data Brazil | Edição 2024-2025; 5.215 respostas tratadas, sendo 5.076 de residentes no Brasil | Pesquisa voluntária sobre carreiras em dados; salários em faixas |
| Questionário do Grupo 12 | 35 respostas a 12 perguntas, coletadas em 2026 | Pesquisa exploratória própria; respostas individuais e resultados restritos fora do Git |
| Matriz de pesquisa G12 | 21 registros de pesquisa documental | Referências e hipóteses, não uma amostra de participantes |

As bases são reais e ficam **separadas por fonte e unidade de observação**. Não
há união de indivíduos entre CAGED e pesquisas. RAIS, PNAD, INEP, Brasscom e Exame
aparecem como referências da matriz, não como datasets importados nesta entrega.

O [guia de dados](inteligencia_de_carreiras/datasets/LEIA-ME.md), o
[catálogo](inteligencia_de_carreiras/datasets/catalogo.md) e as
[regras de integração e privacidade](inteligencia_de_carreiras/datasets/organizacao_e_integracao.md)
detalham procedência e preparação. Os originais e dados tratados completos ficam
locais e são ignorados pelo Git. O dashboard AVD usa somente o
[pacote versionado de agregados públicos](inteligencia_de_carreiras/06_dashboard_e_publicacao/dados_publicos/manifesto.json),
sem depender dos XLSX privados ou dos microdados completos para abrir.

## Executar o Dashboard AVD

Na raiz do repositório, com **Python 3.12**, crie um ambiente próprio para a área
de dados. Isso mantém separadas as dependências da aplicação existente.

```powershell
python -m venv inteligencia_de_carreiras/.venv
$python = ".\inteligencia_de_carreiras\.venv\Scripts\python.exe"
& $python -m pip install -r inteligencia_de_carreiras/06_dashboard_e_publicacao/requirements.txt
& $python -m streamlit run inteligencia_de_carreiras/06_dashboard_e_publicacao/dashboard.py --server.port 8502
```

Abra o endereço local mostrado no terminal, normalmente
[http://localhost:8502](http://localhost:8502). Se a porta estiver ocupada, escolha
outra em `--server.port`. Esse endereço não é uma publicação pública.

O dashboard oferece as visões **Emprego formal**, **Perfis em dados**, **Modelos**
e **Fontes**, com filtros e exportação de agregados. Não é necessário baixar os
datasets completos ou treinar modelos para consultá-lo. Para reproduzir análises
e regenerar o pacote, siga as instruções de cada etapa; a pesquisa própria exige
acesso autorizado aos originais.

## Estado e Limites

- As oito etapas estão implementadas/documentadas; a entrega inicial foi versionada
  no commit `c789019`. Versionar no Git não significa hospedar o dashboard.
- A consolidação registrou **111 testes**, **22 verificações no navegador** e
  **65.761 comparações numéricas sem divergências**, conforme o
  [registro da etapa 07](inteligencia_de_carreiras/07_consolidacao_e_validacao/registro_execucao.json).
- **Ainda pendentes:** revisão estruturada pelo grupo, incorporação de feedback
  real e hospedagem externa seguida de teste remoto. A avaliação técnica não
  substitui validação com usuários nem aprovação acadêmica.
- O recorte CAGED não representa o ano inteiro nem o mercado atual de 2026 e usa
  somente CAGEDMOV, sem os ajustes CAGEDFOR/CAGEDEXC. A pesquisa State of Data não
  representa toda a população de TI.
- Regressão e classificação são análises experimentais com erros e limitações
  documentados; não devem ser usadas para decisões individuais de salário ou contratação.

Os relatórios e PDFs de execução preservam o estado do momento em que foram
gerados, inclusive menções a commit/push então pendentes. Para o estado posterior
ao versionamento, consulte este README e o [índice geral](docs/README.md).

## Registro Original do Ciclo 1

O conteúdo abaixo foi preservado. Seus números, fontes, comandos e afirmações
referem-se **somente à implementação original do Ciclo 1**, com CAGED de janeiro
de 2025; não descrevem todas as fontes ou a situação atual da área AVD.

<details>
<summary>Consultar a documentação original da aplicação existente</summary>


## O que o produto responde

> **Qual é a faixa salarial de entrada (p10/p50/p90) do cargo X, na cidade/UF Y, no emprego
> formal, quanta gente está sendo admitida, e como o salário de entrada se compara ao de saída?**

Tudo em **faixa** (nunca média sozinha), **deflacionado por IPCA**, com **amostra mínima** e
**procedência visível**. A leitura é sempre **agregada**, nunca por pessoa.

## ⚠️ Resultado-chave do Ciclo 1 (verificação crítica)

A promessa original — "medir crescimento salarial dentro do mesmo vínculo e rotatividade
antes de 1 ano" — **não se sustenta** com o Novo CAGED: a base de movimentações **não tem
tempo de vínculo nem identificador de pessoa**. O escopo foi ajustado para o que o dado
realmente entrega (faixa de entrada + fluxos + comparação agregada entrada/saída). Detalhes e
alternativa (RAIS) em [`docs/00_verificacao_layout.md`](docs/00_verificacao_layout.md).

## Dados usados

- **Novo CAGED — Movimentações** (PDET/Ministério do Trabalho), competência **2025-01**
  (4.405.919 movimentações; **39.557** em ocupações de TI). UTF-8, `;`, decimal `,`.
- **IPCA** (API SIDRA/IBGE, tabela 1737/var 2266) como deflator.

## Como rodar

**Pré-requisito:** Python 3.11+ (desenvolvido em 3.12).

```bash
# 1. ambiente virtual + dependências
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium   # para a captura de evidência

# 2. pipeline de dados (bruto -> tratado). Idempotente.
python -m src.ingest_caged         # baixa do FTP, descompacta, -> interim/*.parquet
python -m src.cbo                  # -> processed/cbo_ti.parquet
python -m src.ipca                 # -> processed/ipca.parquet
python -m src.transform            # -> processed/caged_ti.parquet
python -m src.quality_checks       # relatório de qualidade no terminal

# 3. análise exploratória (executa o notebook de ponta a ponta)
jupyter nbconvert --to notebook --execute --inplace notebooks/01_eda.ipynb
#   ou abra no Jupyter: jupyter notebook notebooks/01_eda.ipynb

# 4. dashboard interativo
streamlit run app/dashboard.py

# 5. (opcional) regenerar as 5 evidências em evidencias/
python scripts/capture_evidence.py
```

## O que já existe

| Entregável do ciclo | Artefato |
|---------------------|----------|
| Verificação crítica do layout | `docs/00_verificacao_layout.md` |
| (1) Plano de Análise | `docs/01_plano_de_analise.md` |
| (2) Plano de Preparação | `docs/02_plano_de_preparacao.md` |
| (3) EDA | `notebooks/01_eda.ipynb` (7 gráficos, executado) |
| (4) Dashboard interativo v1 | `app/dashboard.py` |
| Pipeline de dados | `src/ingest_caged.py`, `cbo.py`, `ipca.py`, `transform.py`, `quality_checks.py` |
| Dicionário de variáveis | `docs/dicionario_de_variaveis.md` |
| Evidências | `evidencias/fig1..fig5.png` |
| Log do ciclo | `docs/00_log_do_ciclo.md` |

## Estrutura

```
src/        pipeline (config, ingestão, CBO, IPCA, transformação, QA)
notebooks/  EDA executada
app/        dashboard Streamlit
scripts/    geração de evidências
docs/       verificação, planos, dicionário, log
data/        raw / interim / processed  (NÃO versionado)
evidencias/ PNGs de evidência
```

## Limites declarados da base
O CAGED cobre **apenas emprego formal com carteira (CLT)** — PJ, MEI e informais ficam de
fora. Não mede habilidade técnica nem senioridade. Cada linha é uma **movimentação**
(admissão ou desligamento), não uma pessoa. Neste ciclo há **apenas 1 competência** (2025-01);
séries temporais ficam completas ao adicionar meses em `src/config.py::MESES`.

## Dados são reais
Todos os números deste repositório foram calculados a partir de arquivos reais baixados do
FTP do MTE. **Nenhum dado sintético foi usado.**

</details>
