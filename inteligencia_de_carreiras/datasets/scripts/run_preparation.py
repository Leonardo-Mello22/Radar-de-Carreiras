"""Rebuild or validate the complete package without downloading by default."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_sources(output):
    public_manifest = output / "fontes_manifesto.json"
    private_manifest = output / "fontes_pesquisa_grupo12.json"
    if not public_manifest.exists() or not private_manifest.exists():
        raise FileNotFoundError("Provide the public package and authorized group XLSX files with their manifests before running.")
    public = json.loads(public_manifest.read_text(encoding="utf-8"))
    private = json.loads(private_manifest.read_text(encoding="utf-8"))
    sources = [(output / "brutos" / row["arquivo"], row["sha256"]) for row in public["arquivos_brutos"]]
    sources += [(output / row["arquivo"], row["sha256"]) for row in private["arquivos"]]
    result = []
    for path, expected in sources:
        if not path.exists() or sha256(path) != expected:
            raise ValueError(f"Missing or changed source: {path.name}. Review the manifest before rebuilding.")
        result.append({"arquivo": path.relative_to(output).as_posix(), "sha256": expected})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--temporary", type=Path)
    parser.add_argument("--mode", choices=("full", "validate"), default="full")
    args = parser.parse_args()
    output = args.output.resolve()
    scripts = Path(__file__).resolve().parent
    started = datetime.now(timezone.utc).isoformat()
    sources = verify_sources(output)
    fingerprint = hashlib.sha256(str(output).encode("utf-8")).hexdigest()[:12]
    temporary = args.temporary or Path(tempfile.gettempdir()) / f"radar_carreiras_{fingerprint}" / "caged"
    stages = []

    def run(name, filename, *options):
        before = time.perf_counter()
        print(f"[pipeline] {name}", flush=True)
        subprocess.run([sys.executable, str(scripts / filename), *map(str, options)], check=True)
        stages.append({"etapa": name, "segundos": round(time.perf_counter() - before, 3), "status": "APROVADO"})

    if args.mode == "full":
        run("Preparar fontes publicas", "prepare_datasets.py", "--output", output, "--temporary", temporary)
        run("Preparar pesquisa propria e matriz", "prepare_grupo12.py", "--output", output,
            "--responses", output / "brutos/pesquisa_grupo12/trajetoria_profissional_respostas.xlsx",
            "--matrix", output / "brutos/pesquisa_grupo12/matriz_pesquisa_g12.xlsx")
    run("Validar fontes e exports", "validate_package.py", "--output", output)
    before = time.perf_counter()
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(scripts / "tests"), "-v"], check=True)
    stages.append({"etapa": "Testes", "segundos": round(time.perf_counter() - before, 3), "status": "APROVADO"})
    products = []
    for folder in ("tratados", "auxiliares", "agregados", "modelagem", "qualidade"):
        for path in sorted((output / folder).rglob("*")):
            if path.is_file() and path.suffix in (".csv", ".parquet", ".json") and not path.name.startswith("execucao_"):
                products.append({"arquivo": path.relative_to(output).as_posix(), "sha256": sha256(path)})
    result = {
        "status": "CONCLUIDO_COM_ALERTAS_DOCUMENTADOS", "modo": args.mode,
        "inicio_utc": started, "fim_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "plataforma": platform.system(),
        "dependencias": {name: importlib.metadata.version(name) for name in ("pandas", "numpy", "pyarrow", "py7zr", "openpyxl")},
        "fontes_verificadas": sources, "etapas": stages,
        "codigo_sha256": {path.name: sha256(path) for path in sorted(scripts.glob("*.py"))},
        "produtos": products, "cache": "Temporario externo por padrao; chave por codigo e hashes das fontes.",
        "limite": "Validacao tecnica nao elimina alertas semanticos, comprova representatividade ou autoriza publicacao da pesquisa.",
    }
    report_name = "execucao_preparacao.json" if args.mode == "full" else "execucao_validacao.json"
    (output / "qualidade" / report_name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[done] {len(sources)} fontes verificadas; {len(products)} produtos com SHA-256; modo {args.mode}.", flush=True)


if __name__ == "__main__":
    main()
