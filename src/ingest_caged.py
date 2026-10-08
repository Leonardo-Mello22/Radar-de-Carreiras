"""
Ingestão do Novo CAGED (Base de Movimentações).

Para cada mês pedido (AAAAMM):
  1. baixa o CAGEDMOV<AAAAMM>.7z do FTP do MTE  -> data/raw/
  2. descompacta o .txt                          -> data/interim/
  3. lê o .txt (UTF-8, separador ';', decimal ',') e grava Parquet
                                                   -> data/interim/CAGEDMOV<AAAAMM>.parquet

É IDEMPOTENTE: não rebaixa, não re-extrai e não reconverte o que já existe
(use --force para refazer). Imprime nº de linhas e colunas lidas.

Uso:
    python -m src.ingest_caged                 # usa MESES do config
    python -m src.ingest_caged 202501 202502   # meses específicos
    python -m src.ingest_caged --force 202501  # refaz do zero
"""
from __future__ import annotations

import ftplib
import sys
from pathlib import Path

import pandas as pd
import py7zr

from . import config as cfg


def _ftp_connect() -> ftplib.FTP:
    ftp = ftplib.FTP(cfg.FTP_HOST, timeout=120)
    ftp.login()  # anônimo
    return ftp


def baixar_7z(mes: str, *, force: bool = False) -> Path:
    """Baixa CAGEDMOV<mes>.7z para data/raw/. Idempotente."""
    cfg.RAW.mkdir(parents=True, exist_ok=True)
    destino = cfg.RAW / f"CAGEDMOV{mes}.7z"
    if destino.exists() and not force:
        print(f"[skip] já existe {destino.name} ({destino.stat().st_size/1e6:.1f} MB)")
        return destino

    ano = mes[:4]
    # Caminho no FTP. Os arquivos CAGEDMOV não têm acento, mas o diretório
    # "NOVO CAGED" tem espaço — ftplib lida com isso via cwd separado.
    remoto_dir = f"{cfg.FTP_BASE}/{ano}/{mes}"
    nome = f"CAGEDMOV{mes}.7z"
    print(f"[down] baixando {nome} de ftp://{cfg.FTP_HOST}{remoto_dir}/ ...")
    ftp = _ftp_connect()
    try:
        ftp.cwd(remoto_dir)
        tmp = destino.with_suffix(".7z.part")
        with open(tmp, "wb") as fh:
            ftp.retrbinary(f"RETR {nome}", fh.write)
        tmp.rename(destino)
    finally:
        ftp.quit()
    print(f"[down] ok -> {destino} ({destino.stat().st_size/1e6:.1f} MB)")
    return destino


def descompactar(mes: str, *, force: bool = False) -> Path:
    """Extrai o .txt do .7z para data/interim/. Idempotente."""
    cfg.INTERIM.mkdir(parents=True, exist_ok=True)
    txt = cfg.INTERIM / f"CAGEDMOV{mes}.txt"
    if txt.exists() and not force:
        print(f"[skip] já extraído {txt.name} ({txt.stat().st_size/1e6:.1f} MB)")
        return txt

    arquivo_7z = cfg.RAW / f"CAGEDMOV{mes}.7z"
    if not arquivo_7z.exists():
        raise FileNotFoundError(f"{arquivo_7z} não existe — rode baixar_7z antes.")
    print(f"[7z ] extraindo {arquivo_7z.name} ...")
    with py7zr.SevenZipFile(arquivo_7z, "r") as z:
        z.extractall(path=cfg.INTERIM)
    print(f"[7z ] ok -> {txt} ({txt.stat().st_size/1e6:.1f} MB)")
    return txt


def txt_para_parquet(mes: str, *, force: bool = False) -> Path:
    """Lê o .txt e grava Parquet em data/interim/. Imprime linhas x colunas."""
    parquet = cfg.INTERIM / f"CAGEDMOV{mes}.parquet"
    if parquet.exists() and not force:
        df = pd.read_parquet(parquet)
        print(f"[pq  ] já existe {parquet.name}: {len(df):,} linhas x {df.shape[1]} colunas")
        return parquet

    txt = cfg.INTERIM / f"CAGEDMOV{mes}.txt"
    if not txt.exists():
        raise FileNotFoundError(f"{txt} não existe — rode descompactar antes.")

    print(f"[read] lendo {txt.name} (encoding={cfg.TXT_ENCODING}, sep='{cfg.TXT_SEP}', "
          f"decimal='{cfg.TXT_DECIMAL}') ...")
    # Lemos tudo como string e convertemos no transform, preservando o dado bruto.
    df = pd.read_csv(
        txt,
        sep=cfg.TXT_SEP,
        encoding=cfg.TXT_ENCODING,
        decimal=cfg.TXT_DECIMAL,
        dtype=str,
        na_filter=False,
    )
    print(f"[read] lidas {len(df):,} linhas x {df.shape[1]} colunas")
    print(f"[read] colunas: {list(df.columns)}")
    df.to_parquet(parquet, index=False)
    print(f"[pq  ] gravado -> {parquet} ({parquet.stat().st_size/1e6:.1f} MB)")
    return parquet


def ingerir_mes(mes: str, *, force: bool = False) -> Path:
    baixar_7z(mes, force=force)
    descompactar(mes, force=force)
    return txt_para_parquet(mes, force=force)


def main(argv: list[str]) -> int:
    force = "--force" in argv
    meses = [a for a in argv if a.isdigit() and len(a) == 6] or cfg.MESES
    print(f"=== Ingestão CAGED | meses={meses} | force={force} ===")
    for mes in meses:
        print(f"\n--- {mes} ---")
        ingerir_mes(mes, force=force)
    print("\n=== Ingestão concluída ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
