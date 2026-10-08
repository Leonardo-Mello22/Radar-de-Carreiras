"""
Tradução de código CBO-2002 -> nome legível de ocupação.

A fonte da verdade é a aba 'cbo2002ocupação' do layout oficial do Novo CAGED
(não uma lista digitada à mão). Daí derivamos:
  - o dicionário {código(6) -> nome} de todas as ocupações;
  - o conjunto de códigos pertencentes às famílias de TI (config.CBO_FAMILIAS_TI).

Uso:
    python -m src.cbo            # grava data/processed/cbo_ti.parquet e resume
"""
from __future__ import annotations

import sys
import unicodedata

import pandas as pd

from . import config as cfg


def _titulo(s: str) -> str:
    """Normaliza capitalização ('Diretor de Servicos' -> 'Diretor de Serviços' fica
    como no original; aqui só arrumamos CAIXA, sem inventar acentos)."""
    minusculas = {"de", "da", "do", "das", "dos", "e", "em", "a", "o", "com", "por"}
    palavras = str(s).strip().split()
    out = []
    for i, p in enumerate(palavras):
        pl = p.lower()
        out.append(pl if (pl in minusculas and i > 0) else pl.capitalize())
    return " ".join(out)


def carregar_cbo(layout_xlsx=None) -> pd.DataFrame:
    """Lê a aba de ocupações do layout. Retorna colunas: cbo_codigo, cbo_nome, familia."""
    layout_xlsx = layout_xlsx or cfg.LAYOUT_XLSX
    df = pd.read_excel(layout_xlsx, sheet_name="cbo2002ocupação", dtype=str)
    df.columns = ["cbo_codigo", "cbo_nome"]
    df = df.dropna(subset=["cbo_codigo"])
    df["cbo_codigo"] = df["cbo_codigo"].str.strip()
    df = df[df["cbo_codigo"].str.fullmatch(r"\d{6}")].copy()
    df["cbo_nome"] = df["cbo_nome"].map(_titulo)
    df["familia"] = df["cbo_codigo"].str[:4]
    return df.reset_index(drop=True)


def cbo_ti(layout_xlsx=None) -> pd.DataFrame:
    """Subconjunto das ocupações nas famílias de TI confirmadas."""
    df = carregar_cbo(layout_xlsx)
    ti = df[df["familia"].isin(cfg.CBO_FAMILIAS_TI)].copy()
    return ti.sort_values("cbo_codigo").reset_index(drop=True)


def mapa_codigo_nome(layout_xlsx=None) -> dict[str, str]:
    """Dicionário {cbo_codigo -> cbo_nome} para TODAS as ocupações (tradução geral)."""
    df = carregar_cbo(layout_xlsx)
    return dict(zip(df["cbo_codigo"], df["cbo_nome"]))


def main(argv: list[str]) -> int:
    ti = cbo_ti()
    cfg.PROCESSED.mkdir(parents=True, exist_ok=True)
    ti.to_parquet(cfg.CBO_TI_PARQUET, index=False)
    print(f"Famílias de TI usadas: {cfg.CBO_FAMILIAS_TI}")
    print(f"{len(ti)} ocupações de TI -> {cfg.CBO_TI_PARQUET}\n")
    for fam, grp in ti.groupby("familia"):
        print(f"  família {fam} ({len(grp)}):")
        for _, r in grp.iterrows():
            print(f"    {r.cbo_codigo}  {r.cbo_nome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
