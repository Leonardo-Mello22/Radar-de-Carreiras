# Plano de Preparação de Dados — Entregável 2

> Radar de Carreira em TI · Ciclo 1 · Grupo 12. Cada decisão de limpeza abaixo é
> justificada pelas **características reais** observadas nas variáveis (ver relatório de
> `src/quality_checks.py`), não por suposição.

## 1. Fontes validadas

| Fonte | Status | Formato real verificado |
|-------|--------|-------------------------|
| Novo CAGED — Movimentações (`CAGEDMOV<AAAAMM>.7z`) | ✅ baixada e usada | `.txt` **UTF-8** (não latin-1), sep `;`, decimal `,`, 28 colunas |
| Layout oficial (`.xlsx`) | ✅ baixado e usado | abas de domínio (uf, município, CBO, etc.) |
| IPCA número-índice (SIDRA 1737/2266) | ✅ usado | JSON; 561 meses |

## 2. Desenho do pipeline: bruto → tratado

```
FTP MTE ──download──> data/raw/CAGEDMOV<mm>.7z        (BRUTO, não versionado)
                         │ py7zr
                         ▼
                      data/interim/CAGEDMOV<mm>.txt    (BRUTO descompactado)
                         │ pandas (dtype=str, sem coerção) → preserva o dado cru
                         ▼
                      data/interim/CAGEDMOV<mm>.parquet (espelho fiel em colunar)
                         │ src/transform.py  (filtro TI + tipagem + normalização + deflação)
                         ▼
   data/processed/caged_ti.parquet  +  cbo_ti.parquet  +  ipca.parquet   (TRATADO)
                         │
                         ▼
             EDA (notebook) · Dashboard (Streamlit) · quality_checks
```

**Separação bruto/tratado (princípio central):**
- `data/raw/` e `data/interim/` = **dado bruto**, nunca editado à mão, **não versionado**
  (`.gitignore`). A ingestão é **idempotente**: reexecutar não rebaixa nem recorrompe.
- `data/processed/` = **dado tratado**, 100% reproduzível a partir do bruto rodando o
  pipeline. Nenhum número do produto é digitado — tudo é calculado desses arquivos.
- A leitura inicial do `.txt` é feita com `dtype=str` e `na_filter=False`
  **de propósito**: o Parquet de `interim` é um espelho fiel do arquivo oficial; toda
  conversão/decisão acontece explicitamente em `transform.py`, onde pode ser auditada.

## 3. Decisões de limpeza (cada uma justificada pelo dado real)

| Decisão | O que observamos no dado | Ação tomada |
|---------|--------------------------|-------------|
| **Encoding UTF-8** | Lido como latin-1, "competência"→"competÃªncia" (bytes UTF-8) | ler como `utf-8` (corrige o briefing) |
| **Salário BR → float** | valores como `1800,00`; ponto seria milhar | `replace('.','')` depois `','→'.'` → float |
| **Filtro de ocupações de TI** | só 0,9% das 4,4M linhas são TI | manter apenas famílias CBO confirmadas (`cbo_familia ∈ CBO_FAMILIAS_TI`) |
| **Remover CBO 3173** | 0 ocupações iniciando em 3173 na CBO oficial | família retirada da lista |
| **Adicionar CBO 1425** | é a família real de gerentes de TI (7 ocupações) | adicionada ao recorte |
| **Salários zerados** | 292 linhas com `salário = 0` | marcadas `salario_valido=False` (fora das estatísticas) |
| **Salários < R$300** | 447 linhas (ex.: R$72,46 — jornada por hora/erro) | `salario_valido=False` |
| **Salários > R$200.000** | 10 linhas (prováveis erros de digitação) | `salario_valido=False` |
| **Unidade salarial ≠ mês** | 38.765 de 39.557 são unidade 5 (mês); 527 por hora | mantidas, mas unidade registrada (`unidade_salario_cod`) para transparência |
| **Outliers não são apagados** | — | são **sinalizados** (`salario_valido`), nunca excluídos do arquivo; EDA/dash filtram |
| **Duplicatas (2,39%)** | linhas idênticas existem | **mantidas** — CAGED não tem chave de pessoa; duas movimentações iguais são plausíveis |
| **Normalização de município** | nomes vêm como `Pe-Recife` | remover prefixo `XX-` de UF → `Recife` |
| **Normalização UF/região/sexo/grau/tipo-mov** | vêm como códigos | traduzidos pelas abas de domínio do layout |
| **Idade** | 0 fora da faixa [14, 90] | nenhuma ação necessária (verificado) |
| **Deflação IPCA** | obrigatória por regra de projeto | `salario_real = nominal × índice[ref]/índice[mês]`, ref = `202501` |

> **Nota sobre `salario_real` em jan/2025:** como só há a competência de referência, o fator
> IPCA é 1,0 e `salario_real = salario_nominal`. A deflação passa a ter efeito assim que
> competências de meses diferentes forem ingeridas — a infraestrutura já está pronta.

## 4. Verificações de qualidade (automatizadas)
`src/quality_checks.py` roda e imprime: contagem de registros, nulos por coluna, distribuição
de movimento e de unidade salarial, salários zerados/negativos/suspeitos/absurdos, idade fora
de faixa, duplicatas e as primeiras linhas da base tratada. É a evidência `fig3`.

## 5. Reprodutibilidade
Ordem única para reconstruir todo o dado tratado do zero:
```
python -m src.ingest_caged      # bruto → interim (idempotente)
python -m src.cbo               # cbo_ti.parquet
python -m src.ipca              # ipca.parquet
python -m src.transform         # → data/processed/caged_ti.parquet
python -m src.quality_checks     # relatório de QA
```
Caminhos via `pathlib` (`src/config.py`) — roda em Windows, macOS e Linux.
