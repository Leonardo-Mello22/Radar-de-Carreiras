# 🧭 Radar de Carreira em TI

Painel público e gratuito que traduz **dados oficiais do mercado de trabalho** (Novo CAGED)
em informação útil para decisão de carreira em tecnologia — com foco inicial em
**Pernambuco e Nordeste**.

> **Projeto 5 · CESAR School · 2026.2 · Grupo 12** — Trilha de Análise e Visualização de Dados.
> Este repositório é o resultado do **Ciclo 1** (entregáveis 1, 2, 3 e 4).

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
