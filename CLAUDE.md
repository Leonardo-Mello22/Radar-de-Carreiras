# CLAUDE.md — contexto para futuras sessões

## O produto
**Radar de Carreira em TI** — painel público que traduz os microdados do **Novo CAGED**
(PDET/Ministério do Trabalho) em **faixa salarial de entrada** por cargo/município/UF para
quem está começando em TI (foco Pernambuco/Nordeste). Projeto 5, CESAR School, 2026.2, Grupo 12.

Pergunta central (já ajustada pela realidade do dado): *faixa p10/p50/p90 de entrada do cargo
X na cidade/UF Y, volume de admissões, e comparação agregada entrada×saída.*

## Restrições do projeto (NÃO violar — Seção 5 do briefing)
1. **Faixa, nunca média sozinha.** Todo salário é p10/p50/p90 + tamanho da amostra.
2. **Amostra mínima.** Recorte com menos de `config.MIN_AMOSTRA` (=30) registros **não exibe
   número**, exibe aviso. É uma constante única em `src/config.py`.
3. **Deflação obrigatória.** Nenhuma comparação entre períodos sem corrigir por IPCA.
4. **Procedência visível.** Todo número carrega fonte, mês de referência e amostra.
5. **Sem identificação individual.** Sempre agregado por grupo, nunca por pessoa.
6. **Limites declarados.** Só emprego formal (sem PJ/MEI/informal); não mede habilidade.

## Fatos verificados sobre o dado (não reinventar)
- O `.txt` do CAGEDMOV é **UTF-8** (não latin-1), separador `;`, decimal `,`, **28 colunas**.
- Nomes de arquivo **no FTP** usam latin-1 na URL (`ã`→`%E3`, `ç`→`%E7`); já tratado em `ingest`.
- **Não há** tempo de vínculo nem chave de pessoa → sem trajetória intra-vínculo. Ver
  `docs/00_verificacao_layout.md`. `saldomovimentação`: +1 admissão, −1 desligamento.
- **CBO 3173 não existe**; a gerência de TI é a família **1425** (não 1236). Famílias usadas:
  `config.CBO_FAMILIAS_TI = [1236, 1425, 2122, 2123, 2124, 3171, 3172]`.
- Deflação: SIDRA tabela 1737/var 2266; referência `config.IPCA_MES_REFERENCIA`.

## Estado atual
- Pipeline completo e **idempotente** roda com dados **reais** de **2025-01** (nenhum sintético).
- Base tratada: `data/processed/caged_ti.parquet` (39.557 movimentações de TI, 23 colunas,
  coluna `salario_valido` sinaliza outliers sem apagá-los).
- EDA executada (`notebooks/01_eda.ipynb`), dashboard (`app/dashboard.py`) e 5 evidências prontos.
- **Limitação principal:** só 1 competência → gráficos temporais são um ponto. Adicionar meses
  em `config.MESES` e rerodar o pipeline resolve.
- **`data/` NÃO é versionado** (arquivos excedem o limite do GitHub). É reconstruído rodando o
  pipeline: `python -m src.ingest_caged && python -m src.transform`.

## Identidade visual (ver docs/identidade_visual.md)
- **`app/theme.py` é a FONTE ÚNICA de cores** — nenhum hex em outro `.py`. Importar daí.
- **`src/plotting.py::configurar()`** aplica o estilo do matplotlib uma vez (grade só
  horizontal, sem moldura, uma cor de destaque em laranja, faixa `#FFC08F`, linha de fonte).
- Dashboard: cabeçalho escuro com o aro → filtros em linha (nunca sidebar) → número
  principal → 2 gráficos → rodapé. `theme.aplicar_tema()` na primeira linha.
- Regras: faixa p10/p50/p90 nunca média; "n = X" visível; reais como `R$ 3.240` sem
  centavos; rótulos minúsculos sem ponto; nada de azul nem emoji de interface.

## Stack e convenções
- Python 3.12 em `.venv`. pandas 3.x, pyarrow, duckdb, py7zr, matplotlib (**sem seaborn**),
  streamlit, playwright. Caminhos sempre via `pathlib` (`src/config.py`).
- Commits em português, descritivos. **Nunca** adicionar trailers de atribuição (Co-Authored-By).
