"""
Deflator IPCA — traz salários nominais a preços de um mês de referência único.

Fonte: API SIDRA/IBGE, tabela 1737, variável 2266 (IPCA número-índice,
base dez/1993 = 100). Fórmula de deflação para o mês de referência R:

    valor_real = valor_nominal * ( indice[R] / indice[mês_do_valor] )

Uso:
    python -m src.ipca     # baixa a série, grava data/processed/ipca.parquet, resume
"""
from __future__ import annotations

import sys

import pandas as pd
import requests

from . import config as cfg


def baixar_indice() -> pd.DataFrame:
    """Baixa a série do número-índice do IPCA. Retorna DataFrame: mes(AAAAMM), indice(float)."""
    print(f"[ipca] GET {cfg.SIDRA_IPCA_URL}")
    r = requests.get(cfg.SIDRA_IPCA_URL, timeout=60)
    r.raise_for_status()
    dados = r.json()
    linhas = dados[1:]  # elemento 0 é o cabeçalho de metadados
    df = pd.DataFrame(
        {
            "mes": [row["D3C"] for row in linhas],
            "indice": [float(row["V"]) for row in linhas],
        }
    )
    df = df.dropna().sort_values("mes").reset_index(drop=True)
    print(f"[ipca] {len(df)} meses, de {df['mes'].min()} a {df['mes'].max()}")
    return df


def tabela_deflator(mes_ref: str | None = None) -> pd.DataFrame:
    """DataFrame com fator de deflação para o mês de referência.
    Colunas: mes, indice, fator (= indice[ref]/indice[mes])."""
    mes_ref = mes_ref or cfg.IPCA_MES_REFERENCIA
    df = baixar_indice()
    if mes_ref not in set(df["mes"]):
        raise ValueError(f"Mês de referência {mes_ref} não está na série do IPCA.")
    indice_ref = float(df.loc[df["mes"] == mes_ref, "indice"].iloc[0])
    df["fator"] = indice_ref / df["indice"]
    return df


def deflacionar(
    df: pd.DataFrame, col_valor: str, col_mes: str, mes_ref: str | None = None,
    deflator: pd.DataFrame | None = None,
) -> pd.Series:
    """Retorna a série de valores deflacionados a preços de `mes_ref`.
    `col_mes` deve conter AAAAMM (string)."""
    mes_ref = mes_ref or cfg.IPCA_MES_REFERENCIA
    if deflator is None:
        deflator = tabela_deflator(mes_ref)
    fator_por_mes = dict(zip(deflator["mes"], deflator["fator"]))
    fatores = df[col_mes].astype(str).map(fator_por_mes)
    return df[col_valor] * fatores


def main(argv: list[str]) -> int:
    df = tabela_deflator()
    cfg.PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cfg.IPCA_PARQUET, index=False)
    print(f"Mês de referência: {cfg.IPCA_MES_REFERENCIA} (fator = 1.0)")
    print(df.tail(8).to_string(index=False))
    print(f"-> {cfg.IPCA_PARQUET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
