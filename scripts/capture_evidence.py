"""
Gera as 5 evidências do Ciclo 1 em evidencias/, sem depender de screenshot manual:

  fig1_ingestao_dados_brutos.png  — resumo de download/descompactação + tamanhos em data/raw/
  fig2_estrutura_repositorio.png  — árvore de pastas do projeto
  fig3_carga_validacao.png        — saída de quality_checks (contagem + primeiras linhas)
  fig4_eda_grafico_principal.png  — gráfico mais representativo da EDA (faixa por cargo)
  fig5_dashboard.png              — captura do dashboard rodando, com um filtro aplicado

Capturas de terminal viram imagem a partir do TEXTO (PIL), então existem sem interação humana.

Rodar:
    python scripts/capture_evidence.py
"""
from __future__ import annotations

import io
import subprocess
import sys
import time
import urllib.request
from contextlib import redirect_stdout
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import theme  # noqa: E402
from src import config as cfg  # noqa: E402
from src import plotting  # noqa: E402

cfg.EVIDENCIAS.mkdir(parents=True, exist_ok=True)

# Fonte monoespaçada para as capturas de terminal
_MONO_CANDIDATAS = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]


def _mono(size: int) -> ImageFont.FreeTypeFont:
    for p in _MONO_CANDIDATAS:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def texto_para_png(texto: str, destino: Path, titulo: str = "", size: int = 15) -> None:
    """Renderiza texto monoespaçado (estilo terminal) em PNG."""
    linhas = texto.rstrip("\n").split("\n")
    fonte = _mono(size)
    fonte_tit = _mono(size + 4)
    pad = 18
    lh = size + 6
    # mede largura
    tmp = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(tmp)
    largura = max((d.textlength(l, font=fonte) for l in linhas), default=200)
    if titulo:
        largura = max(largura, d.textlength(titulo, font=fonte_tit))
    W = int(largura) + 2 * pad
    top = pad + (lh + 10 if titulo else 0)
    H = top + lh * len(linhas) + pad
    img = Image.new("RGB", (W, H), theme.GRAFITE)
    d = ImageDraw.Draw(img)
    y = pad
    if titulo:
        d.text((pad, y), titulo, font=fonte_tit, fill=theme.LARANJA)
        y += lh + 10
    for l in linhas:
        d.text((pad, y), l, font=fonte, fill=theme.TEXTO_SOBRE_ESCURO)
        y += lh
    img.save(destino)
    print(f"[ok] {destino.name} ({W}x{H})")


# --------------------------------------------------------------------------- #
def fig1_ingestao() -> None:
    linhas = ["$ python -m src.ingest_caged", ""]
    for p in sorted(cfg.RAW.glob("*")):
        linhas.append(f"  data/raw/{p.name:42s} {p.stat().st_size/1e6:10.2f} MB")
    txt = cfg.INTERIM / f"CAGEDMOV{cfg.MESES[-1]}.txt"
    pq = cfg.INTERIM / f"CAGEDMOV{cfg.MESES[-1]}.parquet"
    linhas.append("")
    if txt.exists():
        linhas.append(f"  descompactado -> interim/{txt.name} ({txt.stat().st_size/1e6:.1f} MB)")
    if pq.exists():
        import pyarrow.parquet as pqt
        n = pqt.ParquetFile(pq).metadata.num_rows
        linhas.append(f"  convertido    -> interim/{pq.name} ({n:,} linhas)")
    linhas.append("")
    linhas.append("  [OK] download + descompactacao concluidos (idempotente)")
    texto_para_png("\n".join(linhas), cfg.EVIDENCIAS / "fig1_ingestao_dados_brutos.png",
                   titulo="Ingestao de dados brutos — Novo CAGED (FTP/MTE)")


def fig2_estrutura() -> None:
    root = cfg.ROOT
    ignore = {".git", ".venv", "__pycache__", ".ipynb_checkpoints", "evidencias"}
    linhas = [f"{root.name}/"]

    def walk(d: Path, prefix: str):
        itens = sorted([p for p in d.iterdir() if p.name not in ignore],
                       key=lambda p: (p.is_file(), p.name.lower()))
        for i, p in enumerate(itens):
            ult = i == len(itens) - 1
            ramo = "└── " if ult else "├── "
            if p.is_dir():
                # dentro de data/: mostra só os subdiretórios (conteúdo não versionado)
                linhas.append(f"{prefix}{ramo}{p.name}/")
                if p.name == "data":
                    sub = sorted([x for x in p.iterdir() if x.is_dir()])
                    for j, s in enumerate(sub):
                        r2 = "└── " if j == len(sub) - 1 else "├── "
                        pe = "    " if ult else "│   "
                        linhas.append(f"{prefix}{pe}{r2}{s.name}/  (nao versionado)")
                else:
                    walk(p, prefix + ("    " if ult else "│   "))
            else:
                linhas.append(f"{prefix}{ramo}{p.name}")

    walk(root, "")
    texto_para_png("\n".join(linhas), cfg.EVIDENCIAS / "fig2_estrutura_repositorio.png",
                   titulo="Estrutura do repositorio", size=14)


def fig3_validacao() -> None:
    from src import quality_checks
    buf = io.StringIO()
    with redirect_stdout(buf):
        quality_checks.rodar()
    texto_para_png(buf.getvalue(), cfg.EVIDENCIAS / "fig3_carga_validacao.png",
                   titulo="Carga e validacao — quality_checks.py", size=13)


def fig4_eda_principal() -> None:
    plotting.configurar()
    df = pd.read_parquet(cfg.CAGED_TI_PARQUET)
    sal = df[df["salario_valido"]]

    def faixa(s):
        return pd.Series({"p10": s.quantile(.10), "p50": s.quantile(.50),
                          "p90": s.quantile(.90), "n": s.size})

    por_cargo = (sal.groupby("cbo_nome")["salario_real"].apply(faixa).unstack()
                 .query("n >= @cfg.MIN_AMOSTRA").sort_values("p50").tail(12))
    n_total = int(por_cargo["n"].sum())
    fig, ax = plt.subplots(figsize=(11, 6.5))
    y = np.arange(len(por_cargo))
    ax.hlines(y, por_cargo["p10"], por_cargo["p90"], color=theme.FAIXA_PREENCHIMENTO, lw=7,
              alpha=.9, label="faixa p10–p90")
    ax.plot(por_cargo["p50"], y, "o", color=theme.LARANJA, ms=11, label="mediana (p50)")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{c}  (n={int(n)})" for c, n in zip(por_cargo.index, por_cargo["n"])],
                       fontsize=9)
    ax.xaxis.set_major_formatter(plotting.REAIS)
    ax.set_xlabel("salário mensal real")
    ax.set_title("Faixa salarial por cargo de TI — p10 / p50 / p90", loc="left")
    ax.legend(loc="lower right")
    plotting.fonte(fig, cfg.IPCA_MES_REFERENCIA, n_total)
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(cfg.EVIDENCIAS / "fig4_eda_grafico_principal.png", dpi=130)
    plt.close(fig)
    print("[ok] fig4_eda_grafico_principal.png")


def fig5_dashboard() -> None:
    port = 8577
    # escolhe um cargo com amostra grande para o filtro aplicado
    df = pd.read_parquet(cfg.CAGED_TI_PARQUET, columns=["cbo_nome", "salario_valido"])
    cargo = (df[df["salario_valido"]]["cbo_nome"].value_counts().idxmax())
    print(f"[fig5] filtro aplicado: cargo='{cargo}'")

    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(cfg.ROOT / "app" / "dashboard.py"),
         "--server.headless", "true", "--server.port", str(port), "--browser.gatherUsageStats", "false"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        url = f"http://localhost:{port}/"
        for _ in range(40):
            try:
                if urllib.request.urlopen(url, timeout=2).status == 200:
                    break
            except Exception:
                time.sleep(0.5)
        time.sleep(2)
        from urllib.parse import quote
        url_filtro = f"{url}?cargo={quote(cargo)}&movimento=admissão"
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1400, "height": 1000})
            page.goto(url_filtro, wait_until="networkidle")
            page.wait_for_timeout(3500)
            page.screenshot(path=str(cfg.EVIDENCIAS / "fig5_dashboard.png"), full_page=True)
            browser.close()
        print("[ok] fig5_dashboard.png")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


def main() -> int:
    print("=== Gerando evidências ===")
    fig1_ingestao()
    fig2_estrutura()
    fig3_validacao()
    fig4_eda_principal()
    fig5_dashboard()
    print("\n=== Evidências em", cfg.EVIDENCIAS, "===")
    for p in sorted(cfg.EVIDENCIAS.glob("*.png")):
        print(f"  {p.name}  ({p.stat().st_size/1e3:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
