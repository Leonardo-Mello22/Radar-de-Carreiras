# Radar de Carreiras

Painel de inteligência de mercado para explorar **salários de entrada, admissões e desligamentos em TI** no Brasil, com recortes para Pernambuco e Nordeste. Reúne dados de emprego formal e pesquisas sobre carreiras em dados, sem combinar populações diferentes.

## Executar o dashboard AVD

Com Python 3.12, na raiz do repositório (PowerShell):

```powershell
python -m venv inteligencia_de_carreiras/.venv
$python = ".\inteligencia_de_carreiras\.venv\Scripts\python.exe"
& $python -m pip install -r inteligencia_de_carreiras/06_dashboard_e_publicacao/requirements.txt
& $python -m streamlit run inteligencia_de_carreiras/06_dashboard_e_publicacao/dashboard.py --server.port 8502
```

Acesse [localhost:8502](http://localhost:8502). O painel carrega agregados do repositório: não precisa baixar microdados nem treinar modelos. As instruções da aplicação original estão no registro do Ciclo 1, abaixo.

## Cobertura dos dados

| Fonte | Período | Registros analisados |
| --- | --- | ---: |
| Novo CAGED (MTE) | Jan/2025 a set/2026 | 842.731 movimentações de TI, das quais 19.200 em PE |
| State of Data Brazil | Edição 2024/2025 | 5.215 respostas tratadas; 5.076 de residentes no Brasil |
| State of Data Brazil | Edição 2025/2026 | 3.494 respostas tratadas; 3.372 de residentes no Brasil |
| Pesquisa própria (CESAR School) | 2026 | 35 respostas, exibidas em agregado |

O CAGED registra **movimentações**, não pessoas únicas nem vagas em aberto. Os salários estão em reais de março de 2025, corrigidos pelo IPCA. As diferenças entre admissões e desligamentos usam apenas os arquivos MOV e não equivalem ao saldo oficial ajustado. As edições do State of Data são amostras voluntárias separadas.

## Resultados e limites

- **Emprego formal:** o painel permite filtrar por período, local e ocupação. As comparações entre 2025 e 2026 usam janeiro a setembro de ambos os anos.
- **Regressão salarial:** o erro médio absoluto foi de **R$ 2.778** no teste de 2026, contra **R$ 3.911** da referência baseada na mediana do treino.
- **Busca ativa de emprego:** ao testar na edição mais recente, o classificador identificou **7,5%** das pessoas que declararam estar buscando emprego. O desempenho não sustenta uso individual.

## Documentação

- [Relatório técnico da atualização](inteligencia_de_carreiras/08_documentacao_final/atualizacao_2025_2026.md): metodologia, resultados e validação.
- [Notebook executado](inteligencia_de_carreiras/03_analise_exploratoria/analise_ampliada.ipynb): análises, gráficos e métricas.
- [Fontes e preparação dos dados](inteligencia_de_carreiras/datasets/ATUALIZACAO_2025_2026.md): procedência, tratamento e reprodução.
- [Guia do dashboard](inteligencia_de_carreiras/06_dashboard_e_publicacao/README.md): execução, testes e publicação.
- [Índice geral](docs/README.md): etapas do projeto e documentação do Ciclo 1.

Projeto desenvolvido pelo Grupo 12 na CESAR School, na trilha de Análise e Visualização de Dados.

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
