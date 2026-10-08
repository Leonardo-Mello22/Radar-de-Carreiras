"""
Transformação: dado bruto (interim) -> dado tratado (processed).

Pipeline:
  1. lê os Parquet brutos de cada mês em data/interim/
  2. filtra ocupações de TI pelas famílias CBO confirmadas (config.CBO_FAMILIAS_TI)
  3. traduz CBO -> nome legível (src.cbo)
  4. normaliza UF, município, região, sexo, grau de instrução (abas do layout oficial)
  5. converte tipos (salário BR -> float, idade -> int, saldo -> int)
  6. deflaciona salários pelo IPCA a preços de config.IPCA_MES_REFERENCIA (src.ipca)
  7. grava data/processed/caged_ti.parquet

Uso:
    python -m src.transform
"""
from __future__ import annotations

import sys

import pandas as pd

from . import cbo as cbo_mod
from . import config as cfg
from . import ipca as ipca_mod


# --------------------------------------------------------------------------- #
# Lookups de domínio — lidos do próprio layout oficial (.xlsx)
# --------------------------------------------------------------------------- #
def _dominio(sheet: str) -> dict[str, str]:
    """Lê uma aba de domínio {Código -> Descrição} como dict de strings."""
    df = pd.read_excel(cfg.LAYOUT_XLSX, sheet_name=sheet, dtype=str)
    df.columns = ["codigo", "descricao"]
    df = df.dropna(subset=["codigo"])
    df["codigo"] = df["codigo"].str.strip()
    return dict(zip(df["codigo"], df["descricao"].str.strip()))


def _limpa_municipio(nome: str) -> str:
    """'Pe-Recife' -> 'Recife'. Remove o prefixo 'XX-' de UF."""
    if not isinstance(nome, str):
        return nome
    if len(nome) > 3 and nome[2] == "-":
        nome = nome[3:]
    return nome.strip()


def _salario_br_para_float(serie: pd.Series) -> pd.Series:
    """'12.500,00' -> 12500.00 ; '1800,00' -> 1800.0. Ponto = milhar, vírgula = decimal."""
    s = serie.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


# --------------------------------------------------------------------------- #
def transformar(meses: list[str] | None = None) -> pd.DataFrame:
    meses = meses or cfg.MESES

    # lookups
    mapa_cbo = cbo_mod.mapa_codigo_nome()
    uf_nome = _dominio("uf")
    mun_nome = _dominio("município")
    regiao_nome = _dominio("região")
    sexo_nome = _dominio("sexo")
    grau_nome = _dominio("graudeinstrução")
    tipomov_nome = _dominio("tipomovimentação")
    deflator = ipca_mod.tabela_deflator()

    partes = []
    for mes in meses:
        p = cfg.INTERIM / f"CAGEDMOV{mes}.parquet"
        if not p.exists():
            raise FileNotFoundError(f"{p} não existe — rode src.ingest_caged {mes}.")
        df = pd.read_parquet(p)
        n0 = len(df)

        # filtro de TI pela família (4 primeiros dígitos do CBO)
        df["cbo_codigo"] = df["cbo2002ocupação"].str.strip()
        df["cbo_familia"] = df["cbo_codigo"].str[:4]
        df = df[df["cbo_familia"].isin(cfg.CBO_FAMILIAS_TI)].copy()
        print(f"[transform] {mes}: {n0:,} linhas -> {len(df):,} de TI "
              f"({len(df)/n0*100:.3f}%)")
        partes.append(df)

    bruto = pd.concat(partes, ignore_index=True)

    # ------- montagem do dataframe tratado -------
    out = pd.DataFrame()
    out["competencia"] = bruto["competênciamov"].str.strip()
    out["uf_codigo"] = bruto["uf"].str.strip()
    out["uf_nome"] = out["uf_codigo"].map(uf_nome)
    out["regiao_nome"] = bruto["região"].str.strip().map(regiao_nome)
    out["municipio_codigo"] = bruto["município"].str.strip()
    out["municipio_nome"] = out["municipio_codigo"].map(mun_nome).map(_limpa_municipio)
    out["cbo_codigo"] = bruto["cbo_codigo"]
    out["cbo_familia"] = bruto["cbo_familia"]
    out["cbo_nome"] = out["cbo_codigo"].map(mapa_cbo)

    saldo = pd.to_numeric(bruto["saldomovimentação"], errors="coerce").astype("Int64")
    out["saldo"] = saldo
    out["movimento"] = saldo.map({1: "admissão", -1: "desligamento"})
    out["tipo_movimentacao_cod"] = bruto["tipomovimentação"].str.strip()
    out["tipo_movimentacao"] = out["tipo_movimentacao_cod"].map(tipomov_nome)

    out["sexo"] = bruto["sexo"].str.strip().map(sexo_nome)
    out["grau_instrucao"] = bruto["graudeinstrução"].str.strip().map(grau_nome)
    out["idade"] = pd.to_numeric(bruto["idade"], errors="coerce").astype("Int64")
    out["horas_contratuais"] = _salario_br_para_float(bruto["horascontratuais"])
    out["unidade_salario_cod"] = bruto["unidadesaláriocódigo"].str.strip()

    out["salario_nominal"] = _salario_br_para_float(bruto["salário"])
    out["salario_real"] = ipca_mod.deflacionar(
        out, "salario_nominal", "competencia", deflator=deflator
    )
    # Sinaliza (não apaga) salários fora da faixa plausível. EDA/dashboard filtram por isto.
    out["salario_valido"] = (
        out["salario_nominal"].notna()
        & (out["salario_nominal"] >= cfg.SAL_MIN_PLAUSIVEL)
        & (out["salario_nominal"] <= cfg.SAL_MAX_PLAUSIVEL)
    )

    out["fonte"] = cfg.FONTE_DADOS
    out["mes_referencia_ipca"] = cfg.IPCA_MES_REFERENCIA

    return out.reset_index(drop=True)


def main(argv: list[str]) -> int:
    df = transformar()
    cfg.PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cfg.CAGED_TI_PARQUET, index=False)
    print(f"\n[transform] gravado -> {cfg.CAGED_TI_PARQUET}")
    print(f"[transform] {len(df):,} movimentações de TI x {df.shape[1]} colunas")
    print(f"[transform] admissões: {(df['movimento']=='admissão').sum():,} | "
          f"desligamentos: {(df['movimento']=='desligamento').sum():,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
