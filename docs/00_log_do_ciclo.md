# Log do Ciclo 1 — Radar de Carreira em TI

> Registro cronológico e honesto do que foi tentado, o que funcionou e o que falhou.
> Grupo 12 · CESAR School · Projeto 5 · 2026.2

---

## Etapa 0 — Reconhecimento (2026-10-08)

Objetivo: verificar se este ambiente alcança a rede e o FTP do MTE, listar o diretório
do Novo CAGED e baixar o layout `.xlsx` e um único mês de `CAGEDMOV`.

### Ambiente

| Item | Resultado |
|------|-----------|
| SO | macOS (Darwin 25.1.0) |
| Python padrão | 3.9.6 (`/usr/bin/python3`) — **abaixo do exigido (3.11+)** |
| Python utilizável | **3.12.13** em `/opt/homebrew/bin/python3.12` ✅ (será o interpretador do venv) |
| Ferramenta 7z no sistema | ❌ não encontrada (`7z`/`7za`/`7zz`) — descompactação será via `py7zr` no venv |

### Testes de rede

**1. API SIDRA (IBGE) — deflator IPCA**
```
curl -s -m 20 -o /dev/null -w "HTTP %{http_code}" \
  "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all"
```
Resultado: **HTTP 200** em ~0,94 s. ✅ Funciona.

**2. Resolução DNS do FTP do MTE**
```
nslookup ftp.mtps.gov.br
```
Resultado: `ftp.mtps.gov.br` → CNAME `ftp.trabalho.gov.br` → **189.9.32.26**. ✅

### Listagem do FTP — Novo CAGED

```
curl -s "ftp://ftp.mtps.gov.br/pdet/microdados/NOVO%20CAGED/"
```
Resultado: **✅ FTP acessível** (anônimo). Conteúdo da raiz:

```
<DIR> 2020  2021  2022  2023  2024  2025  2026  Legado
      293931  Layout Não-identificado Novo Caged Movimentação.xlsx
      345046  Comunicado - Grupamento de Atividades Econômicas.pdf
       83781  Sobre o Novo Caged.pdf
        1084  Leia-me.txt
```

Dentro de `2025/202501/`:
```
    104511  CAGEDEXC202501.7z
    544766  CAGEDFOR202501.7z
  55719173  CAGEDMOV202501.7z   <- usado neste ciclo
```

> ⚠️ **Nota de encoding no FTP:** os nomes de arquivo com acento no servidor estão em
> **latin-1**, não UTF-8. O layout só baixou ao URL-encodar `ã`→`%E3` e `ç`→`%E7`:
> `Layout%20N%E3o-identificado%20Novo%20Caged%20Movimenta%E7%E3o.xlsx`.
> Isso precisa estar codificado no `src/ingest_caged.py`. Arquivos de dados
> (`CAGEDMOV AAAAMM.7z`) não têm acento, então baixam direto.

### Downloads realizados (em `data/raw/`)

| Arquivo | Tamanho | Status | Validação |
|---------|---------|--------|-----------|
| `Layout_Novo_Caged_Movimentacao.xlsx` | 293.931 bytes (287 KB) | HTTP 226 ✅ | `file` → *Microsoft Excel 2007+* |
| `CAGEDMOV202501.7z` | 55.719.173 bytes (53 MB) | HTTP 226 ✅ em ~24 s | `file` → *7-zip archive data, version 0.4* |

### Conclusão da Etapa 0

**Tudo que a Etapa 0 exige funcionou.** O ambiente alcança a rede, o FTP do MTE responde
anonimamente, e tanto o layout oficial quanto um mês real de microdados (jan/2025) foram
baixados e validados no disco. Não há bloqueio para seguir com dados reais — **não será
necessário recorrer a dados sintéticos.**

Pendências levantadas (resolvidas nas próximas etapas, não bloqueiam):
- Descompactar o `.7z` depende de `py7zr` (vai para o `requirements.txt`).
- O venv deve usar explicitamente `python3.12`.
- O encoding latin-1 dos nomes de arquivo no FTP precisa ir codificado na ingestão.

---

## Etapas 1–10 (2026-10-08)

### Obstáculo não-óbvio: Python 3.12 do Homebrew com `pyexpat` quebrado
Ao criar o venv, `ensurepip`/`pip` falhavam com
`Symbol not found: _XML_SetAllocTrackerActivationThreshold`. Causa: o `pyexpat.so` das
bottles de `python@3.12` e `@3.14` linka contra `/usr/lib/libexpat.1.dylib` (do sistema,
sem o símbolo) em vez do `expat` do Homebrew (2.8.4, que tem) — problema conhecido no
macOS 26/Tahoe. `brew reinstall` não resolveu. **Conserto aplicado:**
`install_name_tool -change /usr/lib/libexpat.1.dylib /opt/homebrew/opt/expat/lib/libexpat.1.dylib <pyexpat.so>`
+ `codesign --force --sign -`. Depois disso o venv e o `pip` funcionaram normalmente.

### Execução
- **Etapa 1–2:** esqueleto, venv (Python 3.12), deps instaladas, verificação do layout escrita.
- **Etapa 3:** ingestão do CAGEDMOV 2025-01 → **4.405.919 linhas × 28 colunas** (UTF-8).
- **Etapa 4–5:** dicionário; transformação → **39.557 movimentações de TI** (0,898% do total),
  20.171 admissões / 19.386 desligamentos; QA (292 salários zerados, 447 < R$300, 10 absurdos).
- **Etapa 6:** `01_eda.ipynb` executado ponta a ponta, **0 erros, 7 gráficos** com saídas.
- **Etapa 7:** dashboard Streamlit (testado, HTTP 200).
- **Etapa 8:** planos de análise e preparação.
- **Etapa 9:** 5 evidências geradas (texto→PNG via PIL; matplotlib; Playwright/Chromium).
- **Etapa 10:** README e CLAUDE.md.

**Dados sintéticos:** NÃO foram usados. Todo o ciclo rodou sobre dados reais do FTP do MTE.
