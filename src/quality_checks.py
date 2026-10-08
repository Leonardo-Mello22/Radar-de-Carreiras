"""
Verificações de qualidade sobre a base tratada (data/processed/caged_ti.parquet).

Checa e imprime no terminal: contagem de registros, nulos por coluna, salários
zerados/negativos/absurdos, idades fora de faixa, duplicatas, distribuição por
unidade salarial e por movimento, e as primeiras linhas da base tratada.

Nada aqui "conserta" o dado silenciosamente — apenas reporta, para que as decisões
de limpeza fiquem documentadas (docs/02_plano_de_preparacao.md).

Uso:
    python -m src.quality_checks
"""
from __future__ import annotations

import sys

import pandas as pd

from . import config as cfg

# Limiares de sanidade — fonte única em config.py.
SAL_MIN_PLAUSIVEL = cfg.SAL_MIN_PLAUSIVEL
SAL_MAX_PLAUSIVEL = cfg.SAL_MAX_PLAUSIVEL
IDADE_MIN, IDADE_MAX = cfg.IDADE_MIN, cfg.IDADE_MAX


def rodar(df: pd.DataFrame | None = None) -> pd.DataFrame:
    if df is None:
        df = pd.read_parquet(cfg.CAGED_TI_PARQUET)

    print("=" * 68)
    print("RELATÓRIO DE QUALIDADE — base tratada caged_ti.parquet")
    print("=" * 68)
    print(f"Registros (movimentações de TI): {len(df):,}")
    print(f"Colunas: {df.shape[1]}")
    print(f"Competências: {sorted(df['competencia'].unique())}")
    print(f"Famílias CBO: {sorted(df['cbo_familia'].unique())}")
    print(f"MIN_AMOSTRA (constante única do projeto): {cfg.MIN_AMOSTRA}")

    print("\n--- Nulos por coluna (apenas > 0) ---")
    nulos = df.isna().sum()
    nulos = nulos[nulos > 0]
    if len(nulos):
        for c, n in nulos.items():
            print(f"  {c:24s}: {n:,} ({n/len(df)*100:.2f}%)")
    else:
        print("  nenhum nulo.")

    print("\n--- Movimento (saldo) ---")
    print(df["movimento"].value_counts(dropna=False).to_string())

    print("\n--- Unidade salarial (código -> contagem) ---")
    print(df["unidade_salario_cod"].value_counts(dropna=False).to_string())
    print("  (ver layout: 5=Mês. 'salário' é declarado mensal, mas conferimos a unidade.)")

    print("\n--- Salário nominal: sanidade ---")
    sal = df["salario_nominal"]
    print(f"  nulos/NaN           : {sal.isna().sum():,}")
    print(f"  zerados (==0)       : {(sal == 0).sum():,}")
    print(f"  negativos (<0)      : {(sal < 0).sum():,}")
    print(f"  < {SAL_MIN_PLAUSIVEL:.0f} (suspeito) : {(sal < SAL_MIN_PLAUSIVEL).sum():,}")
    print(f"  > {SAL_MAX_PLAUSIVEL:.0f} (absurdo)  : {(sal > SAL_MAX_PLAUSIVEL).sum():,}")
    validos = sal[(sal >= SAL_MIN_PLAUSIVEL) & (sal <= SAL_MAX_PLAUSIVEL)]
    print(f"  plausíveis          : {len(validos):,} "
          f"(min={validos.min():.2f}, p50={validos.median():.2f}, max={validos.max():.2f})")

    print("\n--- Salário real (deflacionado) ---")
    real = df["salario_real"]
    print(f"  NaN (mês sem IPCA?) : {real.isna().sum():,}")
    print(f"  p10/p50/p90 (válidos): "
          + ", ".join(f"{real.dropna().quantile(q/100):,.2f}" for q in cfg.PERCENTIS))

    print("\n--- Idade: fora de faixa ---")
    idade = df["idade"]
    print(f"  < {IDADE_MIN} ou > {IDADE_MAX}: "
          f"{((idade < IDADE_MIN) | (idade > IDADE_MAX)).sum():,}")
    print(f"  nulas              : {idade.isna().sum():,}")

    print("\n--- Duplicatas (linhas idênticas) ---")
    dup = df.duplicated().sum()
    print(f"  {dup:,} ({dup/len(df)*100:.2f}%)  "
          "[esperado > 0: CAGED não tem chave de pessoa; linhas iguais são plausíveis]")

    print("\n--- Primeiras linhas da base tratada ---")
    cols_preview = ["competencia", "uf_nome", "municipio_nome", "cbo_nome",
                    "movimento", "salario_nominal", "salario_real"]
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(df[cols_preview].head(8).to_string(index=False))

    print("\n" + "=" * 68)
    print("Fim do relatório. (Decisões de limpeza em docs/02_plano_de_preparacao.md)")
    print("=" * 68)
    return df


if __name__ == "__main__":
    rodar()
    sys.exit(0)
