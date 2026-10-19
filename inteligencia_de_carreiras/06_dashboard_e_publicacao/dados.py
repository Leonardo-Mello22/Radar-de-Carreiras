"""Read-only dashboard queries against a checksum-verified aggregate package."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

MIN_N = 30
PERIODS = {"2025T1": "Jan-mar/2025", "202501": "Jan/2025", "202502": "Fev/2025", "202503": "Mar/2025"}
FORBIDDEN = {"respondente_id", "registro_id", "salario_real", "salario_nominal", "genero", "raca_cor"}
REQUIRED_FILES = {"emprego.parquet", "perfis.parquet", "distribuicoes.parquet", "tecnologias.parquet",
                  "R1_teste_marco.csv", "R1_ajuste_jan_fev.csv", "R3_observado_previsto.png", "R4_residuos.png",
                  "C1_metricas_teste.csv", "C4_curvas_roc.csv", "C5_curvas_precision_recall.csv"}


class PackageError(ValueError):
    pass


def load_package(folder):
    folder = Path(folder)
    try:
        metadata = json.loads((folder / "manifesto.json").read_text(encoding="utf-8"))
        if not REQUIRED_FILES.issubset(metadata["arquivos"]) or metadata["minimo_estatistico"] != MIN_N:
            raise PackageError("Manifesto incompleto ou regra estatistica incompatível.")
        for name, detail in metadata["arquivos"].items():
            if Path(name).name != name:
                raise PackageError("Nome de arquivo invalido no manifesto.")
            with (folder / name).open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual != detail["sha256"] or (folder / name).stat().st_size != detail["bytes"]:
                raise PackageError("O pacote de dados precisa ser revalidado.")
        package = {"metadata": metadata}
        for name in ["emprego", "perfis", "distribuicoes", "tecnologias"]:
            frame = pd.read_parquet(folder / f"{name}.parquet")
            if FORBIDDEN.intersection(frame.columns):
                raise PackageError("O pacote contem campos individuais nao permitidos.")
            package[name] = frame
        for name in ["R1_teste_marco", "C1_metricas_teste", "C4_curvas_roc", "C5_curvas_precision_recall"]:
            frame = pd.read_csv(folder / f"{name}.csv")
            if FORBIDDEN.intersection(frame.columns):
                raise PackageError("Tabela de modelos contem campos individuais.")
            package[name] = frame
        return package
    except (OSError, KeyError, ValueError, TypeError) as error:
        raise PackageError("Pacote publico indisponivel ou incompleto.") from error


def geography(region, uf):
    if region == "Pernambuco":
        return "UF_PE"
    if uf != "Todas":
        return "UF_" + uf
    return "NE" if region == "Nordeste" else "BR"


def occupation(area, cargo):
    if cargo != "Todos":
        return "cargo", cargo
    if area != "Todas":
        return "area", area
    return "total", "Todos"


def caged_query(package, geo, period, kind="total", category="Todos"):
    table = package["emprego"]
    return table[table.geo.eq(geo) & table.periodo.eq(period) & table.tipo.eq(kind) & table.categoria.eq(category)].copy()


def caged_groups(package, geo, period, area, cargo):
    table = package["emprego"]
    kind = "area" if area == "Todas" and cargo == "Todos" else "cargo"
    groups = table[table.geo.eq(geo) & table.periodo.eq(period) & table.tipo.eq(kind)]
    if area != "Todas":
        groups = groups[groups.area.eq(area)]
    if cargo != "Todos":
        groups = groups[groups.categoria.eq(cargo)]
    return groups.copy()


def profile_query(package, geo, seniority, work):
    result = {}
    for key in ["perfis", "distribuicoes", "tecnologias"]:
        table = package[key]
        result[key] = table[table.geo.eq(geo) & table.senioridade.eq(seniority) & table.modelo.eq(work)].copy()
    return result


def export_csv(frame):
    if FORBIDDEN.intersection(frame.columns):
        raise PackageError("Exportacao individual nao permitida.")
    return frame.to_csv(index=False).encode("utf-8-sig")
