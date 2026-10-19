"""Download public sources into a standalone dataset package."""
from __future__ import annotations

import argparse
import ftplib
import gzip
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FTP_HOST = "ftp.mtps.gov.br"
FTP_BASE = "/pdet/microdados/NOVO CAGED"
SURVEY_URL = (
    "https://raw.githubusercontent.com/letsdata/challenge-data-hackers-2025/main/"
    "aula01/script/data/raw/"
    + urllib.parse.quote("Final Dataset - State of Data 2024 - Kaggle - df_survey_2024.zip")
)


def download_http(url: str, target: Path) -> None:
    if target.exists():
        return
    request = urllib.request.Request(url, headers={"User-Agent": "RadarDataset/1.0"})
    temporary = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(request, timeout=90) as response, temporary.open("wb") as out:
        while chunk := response.read(1024 * 1024):
            out.write(chunk)
    temporary.replace(target)
    print(f"[download] {target.name}: {target.stat().st_size / 1e6:.1f} MB", flush=True)


def download_ftp(directory: str, name: str, target: Path) -> None:
    for attempt in range(3):
        ftp = ftplib.FTP(FTP_HOST, timeout=120, encoding="latin-1")
        try:
            ftp.login()
            ftp.cwd(directory)
            ftp.voidcmd("TYPE I")
            expected = ftp.size(name)
            if target.exists() and target.stat().st_size == expected:
                print(f"[cache] {target.name}", flush=True)
                return
            temporary = target.with_suffix(target.suffix + ".part")
            received = 0
            last = time.monotonic()
            with temporary.open("wb") as out:
                def receive(chunk: bytes) -> None:
                    nonlocal received, last
                    out.write(chunk)
                    received += len(chunk)
                    if time.monotonic() - last >= 20:
                        print(f"[download] {name}: {received / 1e6:.1f}/{expected / 1e6:.1f} MB", flush=True)
                        last = time.monotonic()
                ftp.retrbinary(f"RETR {name}", receive, blocksize=1024 * 1024)
            if received != expected:
                raise ValueError(f"Incomplete download: {received} != {expected}")
            temporary.replace(target)
            print(f"[download] {target.name}: {received / 1e6:.1f} MB", flush=True)
            return
        except (OSError, ftplib.Error, ValueError) as error:
            print(f"[retry] {name}: {error}", flush=True)
            if attempt == 2:
                raise
        finally:
            ftp.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.output / "brutos"
    raw.mkdir(parents=True, exist_ok=True)
    download_http(SURVEY_URL, raw / "state_of_data_2024_2025.zip")
    download_http("https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/202501-202503", raw / "ipca_2025_01_03.json")
    download_http("https://servicodados.ibge.gov.br/api/v1/localidades/municipios", raw / "municipios_ibge.json")
    with ftplib.FTP(FTP_HOST, timeout=60, encoding="latin-1") as ftp:
        ftp.login()
        ftp.cwd(FTP_BASE)
        layout = next(name for name in ftp.nlst() if name.startswith("Layout") and name.endswith(".xlsx"))
    download_ftp(FTP_BASE, layout, raw / "layout_novo_caged.xlsx")
    for month in ("202501", "202502", "202503"):
        download_ftp(f"{FTP_BASE}/2025/{month}", f"CAGEDMOV{month}.7z", raw / f"CAGEDMOV{month}.7z")
    # HTTP compression is transport encoding, not part of the JSON dataset.
    for path in raw.glob("*.json"):
        if path.read_bytes()[:2] == b"\x1f\x8b":
            path.write_bytes(gzip.decompress(path.read_bytes()))
    sources = []
    for path in sorted(raw.iterdir()):
        if not path.is_file() or path.suffix == ".part":
            continue
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        sources.append({"arquivo": path.name, "bytes": path.stat().st_size, "sha256": digest})
    manifest = {
        "baixado_em_utc": datetime.now(timezone.utc).isoformat(),
        "caged_meses": ["202501", "202502", "202503"],
        "caged_fonte": f"ftp://{FTP_HOST}{FTP_BASE}/2025/",
        "state_of_data_fonte_original": "https://www.kaggle.com/datasets/datahackers/state-of-data-brazil-20242025",
        "state_of_data_espelho_download": SURVEY_URL,
        "ipca_fonte": "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/202501-202503",
        "municipios_fonte": "https://servicodados.ibge.gov.br/api/v1/localidades/municipios",
        "arquivos_brutos": sources,
    }
    (args.output / "fontes_manifesto.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[done] Sources downloaded and checksummed.", flush=True)


if __name__ == "__main__":
    main()
