"""Expand public data without changing the inputs of the original deliverables."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from download_sources import FTP_BASE, FTP_HOST, download_ftp, download_http

ROOT = Path(__file__).resolve().parents[1]
BATCH = "atualizacao_2025_2026"
MONTHS = [f"{year}{month:02}" for year, end in [(2025, 12), (2026, 9)]
          for month in range(1, end + 1)]
SURVEY_URL = (
    "https://raw.githubusercontent.com/data-hackers-br/state-of-data-brazil/main/"
    "data/raw/2025-2026/state_of_data_2025_2026.csv"
)
IPCA_URL = f"https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/{MONTHS[0]}-{MONTHS[-1]}"
SURVEY_FILE = "state_of_data_2025_2026.csv"
IPCA_FILE = "ipca_2025_2026.json"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(".json.part")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def fetch(root: Path) -> None:
    original = root / "brutos"
    raw = original / BATCH
    raw.mkdir(parents=True, exist_ok=True)
    legacy = json.loads((root / "fontes_manifesto.json").read_text(encoding="utf-8"))
    verified = {entry["arquivo"]: entry["sha256"] for entry in legacy["arquivos_brutos"]}
    sources = {}
    for name, url in [(SURVEY_FILE, SURVEY_URL), (IPCA_FILE, IPCA_URL)]:
        download_http(url, raw / name)
        sources[name] = url
    for name in ("layout_novo_caged.xlsx", "municipios_ibge.json"):
        if sha256(original / name) != verified[name]:
            raise ValueError(f"Legacy reference does not match its manifest: {name}")
        if not (raw / name).exists():
            shutil.copyfile(original / name, raw / name)
        if sha256(raw / name) != verified[name]:
            raise ValueError(f"Copied reference does not match its manifest: {name}")
        sources[name] = "fontes_manifesto.json"

    def fetch_month(month: str) -> tuple[str, str]:
        name = f"CAGEDMOV{month}.7z"
        directory = f"{FTP_BASE}/{month[:4]}/{month}"
        source, target = original / name, raw / name
        if source.is_file() and verified.get(name) == sha256(source):
            if not target.exists():
                shutil.copyfile(source, target)
            if sha256(target) != verified[name]:
                raise ValueError(f"Copied archive does not match its manifest: {name}")
            print(f"[cache] {name}", flush=True)
        else:
            download_ftp(directory, name, target)
        return name, f"ftp://{FTP_HOST}{directory}/{name}"

    with ThreadPoolExecutor(max_workers=4) as executor:
        sources.update(executor.map(fetch_month, MONTHS))
    write_json(raw / "manifesto.json", {
        "baixado_em_utc": datetime.now(timezone.utc).isoformat(),
        "caged_meses": MONTHS,
        "caged_tipo": "CAGEDMOV",
        "arquivos": {
            name: {"fonte": url, "bytes": (raw / name).stat().st_size, "sha256": sha256(raw / name)}
            for name, url in sources.items()
        },
    })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    fetch(args.root)


if __name__ == "__main__":
    main()
