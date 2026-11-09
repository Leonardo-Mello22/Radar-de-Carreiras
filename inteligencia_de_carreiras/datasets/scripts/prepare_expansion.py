"""Prepare the expanded CAGED and survey as a separate, versioned data batch."""
from __future__ import annotations

import argparse
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import py7zr

from expand_public_sources import BATCH, IPCA_FILE, MONTHS, ROOT, SURVEY_FILE, sha256, write_json
from prepare_datasets import (
    NE, REF, clean_text, enrich_caged, load_domains, municipality_table,
    nullable_boolean, read_json, slug, survey_salary_bounds,
)


def write_parquet(frame: pd.DataFrame, target: Path) -> None:
    temporary = target.with_suffix(".parquet.part")
    frame.to_parquet(temporary, index=False)
    temporary.replace(target)


def prepare_month(raw: Path, output: Path, month: str, wait_seconds: int) -> dict:
    archive_path = raw / f"CAGEDMOV{month}.7z"
    deadline = time.monotonic() + wait_seconds
    while not archive_path.is_file() and time.monotonic() < deadline:
        time.sleep(2)
    digest = sha256(archive_path)
    factors = {row["D3C"]: float(row["V"]) for row in read_json(raw / IPCA_FILE)[1:]}
    if not set(MONTHS).issubset(factors) or min(factors.values()) <= 0:
        raise ValueError("IPCA does not cover the entire period")
    reference = factors[REF]
    factors = {key: reference / value for key, value in factors.items()}
    domains, municipalities = load_domains(raw), municipality_table(raw)
    total, parts = 0, []
    with TemporaryDirectory(prefix=f"radar_{month}_", dir=output) as stage:
        with py7zr.SevenZipFile(archive_path) as archive:
            members = [name for name in archive.getnames() if name.lower().endswith(".txt")]
            if len(members) != 1 or Path(members[0]).name != members[0] or ":" in members[0] or "\\" in members[0]:
                raise ValueError(f"Unexpected archive members: {members}")
            archive.extract(path=stage, targets=members)
        for chunk in pd.read_csv(Path(stage) / members[0], sep=";", dtype=str,
                                 encoding="utf-8-sig", chunksize=500_000, keep_default_na=False):
            parts.append(enrich_caged(chunk.reset_index(drop=True), month, total, domains, municipalities, factors))
            total += len(chunk)
    frame = pd.concat(parts, ignore_index=True)
    if (frame.empty or not frame.competencia.eq(month).fillna(False).all()
            or not frame.saldo.isin([1, -1]).all() or not frame.registro_id.is_unique
            or frame.loc[frame.salario_valido, "salario_real"].isna().any()):
        raise ValueError(f"Invalid CAGED data for {month}")
    write_parquet(frame, output / "caged_ti" / f"{month}.parquet")

    group_keys = ["uf_sigla", "area_ti", "movimento"]
    counts = frame.groupby(group_keys, dropna=False).size().rename("movimentacoes")
    salary = frame.loc[frame.salario_valido].groupby(group_keys, dropna=False).salario_real
    sample = salary.size().rename("registros_salario_valido")
    percentiles = salary.quantile([.1, .5, .9]).unstack().set_axis(
        ["salario_real_p10", "salario_real_p50", "salario_real_p90"], axis=1)
    percentiles = percentiles.where(sample.ge(30), axis=0)
    aggregate = counts.to_frame().join([sample, percentiles]).reset_index()
    aggregate["registros_salario_valido"] = aggregate["registros_salario_valido"].fillna(0).astype(int)
    aggregate.insert(0, "competencia", month)
    aggregate["mes_referencia_ipca"] = REF
    write_parquet(aggregate, output / "caged_indicadores" / f"{month}.parquet")
    print(f"[caged] {month}: {len(frame):,} TI / {total:,} brutas", flush=True)
    return {
        "competencia": month, "sha256_origem": digest, "linhas_brutas": total,
        "movimentacoes_ti": len(frame), "admissoes_ti": int(frame.saldo.eq(1).sum()),
        "desligamentos_ti": int(frame.saldo.eq(-1).sum()),
        "movimentacoes_pe": int(frame.uf_sigla.eq("PE").sum()),
        "movimentacoes_nordeste": int(frame.uf_sigla.isin(NE).sum()),
        "salarios_validos": int(frame.salario_valido.sum()),
        "cbo_sem_descricao": int(frame.cbo_nome.isna().sum()),
        "municipios_sem_descricao": int(frame.municipio_nome.isna().sum()),
    }


SURVEY_FIELDS = {
    "1.a_idade": "idade", "1.g_vive_no_brasil": "vive_no_brasil",
    "1.i.1_uf_onde_mora": "uf_sigla", "1.i.2_regiao_onde_mora": "regiao_nome",
    "1.l_nivel_de_ensino": "nivel_ensino", "2.a_situacao_de_trabalho": "situacao_trabalho",
    "2.d_atua_como_gestor": "atua_como_gestor", "2.f_cargo_atual": "cargo_atual",
    "2.g_nivel": "senioridade_declarada", "2.h_faixa_salarial": "faixa_salarial_declarada",
    "2.i_tempo_de_experiencia_em_dados": "experiencia_dados_faixa",
    "2.n_planos_de_mudar_de_emprego_6m": "planos_mudar_emprego_6m",
    "2.q_modelo_de_trabalho_atual": "modelo_trabalho_declarado",
    "4.c.1_SQL": "usa_sql", "4.c.2_R": "usa_r", "4.c.3_Python": "usa_python",
    "4.e.1_Amazon Web Services (AWS)": "usa_aws", "4.e.2_Google Cloud (GCP)": "usa_gcp",
    "4.e.3_Azure (Microsoft)": "usa_azure", "4.g.1_Microsoft PowerBI": "usa_power_bi",
}


def prepare_survey(raw: Path, output: Path) -> dict:
    original = pd.read_csv(raw / SURVEY_FILE, low_memory=False)
    unique = original.drop_duplicates()
    columns = {slug(column): column for column in unique.columns}
    resolved = {columns[slug(source)]: target for source, target in SURVEY_FIELDS.items()}
    result = unique[list(resolved)].rename(columns=resolved).copy()
    for column in result.columns:
        if column in ("vive_no_brasil", "atua_como_gestor") or column.startswith("usa_"):
            values = clean_text(result[column]).replace({"0.0": "0", "1.0": "1"})
            result[column] = nullable_boolean(values)
        elif column == "idade":
            result[column] = pd.to_numeric(result[column], errors="raise").astype("Int64")
        else:
            result[column] = clean_text(result[column])
    result["uf_sigla"] = result.uf_sigla.str.upper()
    result["senioridade_declarada"] = result.senioridade_declarada.map(slug).map({
        "junior": "Junior", "pleno": "Pleno", "senior": "Senior", "especialista_staff": "Especialista/Staff+",
    }).astype("string")
    result["vinculo_grupo"] = result.situacao_trabalho.map(slug).map({
        "empregado_clt": "CLT", "empreendedor_ou_empregado_cnpj": "PJ ou empreendedor",
        "estagiario": "Estagio", "servidor_publico": "Servidor publico", "freelancer": "Freelancer",
        "somente_estudante_graduacao": "Estudante", "somente_estudante_pos_graduacao": "Estudante",
        "desempregado_buscando_recolocacao": "Desempregado",
        "desempregado_e_nao_estou_buscando_recolocacao": "Desempregado",
        "trabalho_na_area_academica_pesquisador": "Academico ou pesquisador",
        "vivo_no_brasil_e_trabalho_remoto_para_empresa_de_fora_do_brasil": "Trabalho internacional",
        "vivo_fora_do_brasil_e_trabalho_para_empresa_de_fora_do_brasil": "Trabalho internacional",
    }).astype("string").fillna("Nao informado")
    result["modelo_trabalho"] = result.modelo_trabalho_declarado.map(slug).map({
        "modelo_100_remoto": "Remoto", "modelo_100_presencial": "Presencial",
    }).astype("string")
    result.loc[result.modelo_trabalho_declarado.map(slug).str.startswith("modelo_hibrido"),
               "modelo_trabalho"] = "Hibrido"
    result["modelo_trabalho"] = result.modelo_trabalho.fillna("Nao informado")
    intervals = pd.DataFrame(result.faixa_salarial_declarada.map(survey_salary_bounds).tolist(),
                             index=result.index, columns=["faixa_salario_limite_inferior",
                             "faixa_salario_limite_superior", "faixa_limite_superior_exclusivo"])
    low, high = intervals.iloc[:, 0], intervals.iloc[:, 1]
    invalid = low.notna() & high.notna() & low.ge(high)
    intervals.loc[invalid, :] = pd.NA
    result = result.join(intervals.astype({"faixa_limite_superior_exclusivo": "boolean"}))
    result["faixa_salarial_invalida"] = invalid
    result.insert(0, "respondente_id", [f"SOD2025:{index + 2}" for index in result.index])
    result.insert(0, "edicao", "2025/2026")
    br = result.loc[result.vive_no_brasil.fillna(False)]
    write_parquet(result, output / "state_of_data_2025_2026.parquet")
    write_parquet(br, output / "state_of_data_brasil_2025_2026.parquet")
    write_json(output / "state_of_data_mapa_colunas.json", resolved)
    print(f"[survey] {len(result):,} respostas tratadas; {len(br):,} Brasil", flush=True)
    return {
        "edicao": "2025/2026", "respostas_brutas": len(original), "colunas_brutas": original.shape[1],
        "respostas_tratadas": len(result), "respostas_brasil": len(br),
        "respostas_pe": int(br.uf_sigla.eq("PE").sum()),
        "duplicatas_exatas_removidas": len(original) - len(result),
        "faixas_salariais_invalidas": int(invalid.sum()),
    }


def prepare(root: Path, workers: int, wait_seconds: int) -> None:
    raw, output = root / "brutos" / BATCH, root / "tratados" / BATCH
    for folder in ("caged_ti", "caged_indicadores"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    survey = prepare_survey(raw, output)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        tasks = [executor.submit(prepare_month, raw, output, month, wait_seconds) for month in MONTHS]
        controls = [task.result() for task in tasks]
    manifest = read_json(raw / "manifesto.json")
    if manifest["caged_meses"] != MONTHS:
        raise ValueError("Raw manifest and CAGED periods do not match")
    for name, entry in manifest["arquivos"].items():
        if sha256(raw / name) != entry["sha256"] or (raw / name).stat().st_size != entry["bytes"]:
            raise ValueError(f"Raw source integrity check failed: {name}")
    for control in controls:
        name = f"CAGEDMOV{control['competencia']}.7z"
        if manifest["arquivos"][name]["sha256"] != control["sha256_origem"]:
            raise ValueError(f"Source changed during preparation: {name}")
    frame = pd.DataFrame(controls)
    write_parquet(frame, output / "controle_caged_mensal.parquet")
    write_json(output / "resumo.json", {
        "caged_tipo": "CAGEDMOV", "caged_referencia_ipca": REF, "caged_meses": MONTHS,
        "caged_2025": int(frame.loc[frame.competencia.str.startswith("2025"), "movimentacoes_ti"].sum()),
        "caged_2026": int(frame.loc[frame.competencia.str.startswith("2026"), "movimentacoes_ti"].sum()),
        "caged_total": int(frame.movimentacoes_ti.sum()), "caged_total_bruto": int(frame.linhas_brutas.sum()),
        "state_of_data": survey, "manifesto_bruto_sha256": sha256(raw / "manifesto.json"),
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--wait-seconds", type=int, default=0,
                        help="Wait for pending monthly archives when download is running separately.")
    args = parser.parse_args()
    prepare(args.root, args.workers, args.wait_seconds)
