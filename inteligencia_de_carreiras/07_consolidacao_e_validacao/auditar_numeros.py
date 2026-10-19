"""Reconcile every dashboard slice against prepared sources, independently of its builder."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np
import pandas as pd

AREA = Path(__file__).resolve().parent
DASHBOARD = AREA.parent / "06_dashboard_e_publicacao"
sys.path.insert(0, str(DASHBOARD))
from dados import load_package

NE = {"MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"}
TECH = {"SQL": "usa_sql", "Python": "usa_python", "R": "usa_r", "Power BI": "usa_power_bi",
        "AWS": "usa_aws", "GCP": "usa_gcp", "Azure": "usa_azure"}
TARGET_YES = {"Estou em busca de oportunidades dentro ou fora do Brasil",
              "Estou em busca de oportunidades, mas apenas fora do Brasil"}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class Audit:
    def __init__(self):
        self.checks = Counter()
        self.failures = []
        self.n_failures = 0

    def equal(self, group, key, actual, expected):
        self.checks[group] += 1
        if isinstance(expected, (float, int, np.number)):
            ok = pd.isna(actual) if pd.isna(expected) else pd.notna(actual) and np.isclose(actual, expected, rtol=1e-12, atol=1e-7)
        else:
            ok = actual == expected
        if not ok:
            self.n_failures += 1
            if len(self.failures) < 50:
                self.failures.append({"grupo": group, "recorte": str(key), "obtido": str(actual), "esperado": str(expected)})


def regional(source, geo):
    if geo == "BR":
        return source
    return source[source.uf_sigla.isin(NE)] if geo == "NE" else source[source.uf_sigla.eq(geo[3:])]


def salary_statistics(frame):
    result = {"n_eventos": len(frame)}
    for movement, name in [(1, "admissoes"), (-1, "desligamentos")]:
        rows = frame[frame.saldo.eq(movement)]
        valid = pd.Series(rows.loc[rows.salario_valido.fillna(False), "salario_real"].to_numpy(dtype=float))
        result[name] = len(rows)
        result[name + "_validos"] = len(valid)
        for label, quantile in [("p10", .1), ("p50", .5), ("p90", .9)]:
            result[name + "_" + label] = valid.quantile(quantile) if len(valid) >= 30 else np.nan
    result["diferenca_mov"] = result["admissoes"] - result["desligamentos"]
    return result


def audit_caged(package, source, audit):
    table = package["emprego"]
    keys = ["geo", "periodo", "tipo", "categoria"]
    audit.equal("estrutura_caged", "chaves duplicadas", int(table.duplicated(keys).sum()), 0)
    expected_keys = {(geo, period, item["tipo"], item["categoria"])
                     for geo in ["BR", "NE", *["UF_" + u for u in source.uf_sigla.dropna().unique()]]
                     for period in ["2025T1", "202501", "202502", "202503"] for item in package["metadata"]["catalogo"]}
    audit.equal("estrutura_caged", "recortes completos", set(table[keys].itertuples(index=False, name=None)) == expected_keys, True)
    for (geo, period), rows in table.groupby(["geo", "periodo"], observed=True):
        frame = regional(source, geo)
        if period != "2025T1":
            frame = frame[frame.competencia.eq(period)]
        for row in rows.itertuples(index=False):
            selected = frame
            if row.tipo != "total":
                field = "area_ti" if row.tipo == "area" else "cbo_codigo"
                selected = frame[frame[field].eq(row.categoria)]
            for field, expected in salary_statistics(selected).items():
                audit.equal("caged_contagens_e_quantis", (geo, period, row.tipo, row.categoria, field), getattr(row, field), expected)
    return len(table)


def grouped_frequencies(series):
    counts = series.dropna().astype(str).value_counts()
    result = counts[counts >= 5].to_dict()
    if counts.lt(5).any():
        result["Outras respostas (categorias pequenas)"] = int(counts[counts < 5].sum())
    return result


def audit_profiles(package, source, audit):
    summary = package["perfis"]
    keys = ["geo", "senioridade", "modelo"]
    for name, extra in [("perfis", []), ("distribuicoes", ["variavel", "categoria"]), ("tecnologias", ["tecnologia"])]:
        table = package[name]
        audit.equal("estrutura_perfis", name + " duplicados", int(table.duplicated(keys + extra).sum()), 0)
        audit.equal("estrutura_perfis", name + " recortes conhecidos", set(table[keys].itertuples(index=False, name=None)).issubset(set(summary[keys].itertuples(index=False, name=None))), True)
    expected_keys = {(geo, senior, model) for geo in ["BR", "NE", *["UF_"+u for u in source.uf_sigla.dropna().unique()]]
                     for senior in ["Todos", "Junior", "Pleno", "Senior", "Nao informado"]
                     for model in ["Todos", "Remoto", "Hibrido", "Presencial", "Nao informado"]}
    audit.equal("estrutura_perfis", "recortes completos", set(summary[keys].itertuples(index=False, name=None)) == expected_keys, True)
    dist_groups = dict(tuple(package["distribuicoes"].groupby(keys, observed=True)))
    tech_groups = dict(tuple(package["tecnologias"].groupby(keys, observed=True)))
    for row in summary.itertuples(index=False):
        key = (row.geo, row.senioridade, row.modelo)
        frame = regional(source, row.geo)
        if row.senioridade != "Todos":
            frame = frame[frame.senioridade_declarada.fillna("Nao informado").eq(row.senioridade)]
        if row.modelo != "Todos":
            frame = frame[frame.modelo_trabalho.eq(row.modelo)]
        target = frame.planos_mudar_emprego_6m.dropna()
        active = int(target.isin(TARGET_YES).sum())
        expected = {"n_respostas": len(frame), "n_salarios": int(frame.faixa_salarial_declarada.notna().sum()),
                    "n_alvo": len(target), "n_ativos": active if len(target) >= 30 else np.nan,
                    "proporcao_ativa": active/len(target) if len(target) >= 30 else np.nan}
        for field, value in expected.items():
            audit.equal("perfis_contagens_e_alvo", (*key, field), getattr(row, field), value)
        actual_dist = dist_groups.get(key, package["distribuicoes"].iloc[:0])
        actual_tech = tech_groups.get(key, package["tecnologias"].iloc[:0])
        if len(frame) < 30:
            audit.equal("supressao_perfis", key, len(actual_dist) + len(actual_tech), 0)
            continue
        for field, variable in [("faixa_salarial_declarada", "salario"), ("nivel_ensino", "formacao"), ("vinculo_grupo", "vinculo")]:
            valid = frame[field].dropna()
            expected_freq = grouped_frequencies(valid) if len(valid) >= 30 else {}
            actual = actual_dist[actual_dist.variavel.eq(variable)]
            audit.equal("distribuicoes_categorias", (*key, variable), actual.set_index("categoria").n.to_dict() == expected_freq, True)
            for record in actual.itertuples(index=False):
                audit.equal("distribuicoes_bases", (*key, variable, record.categoria), record.denominador, len(valid))
                audit.equal("distribuicoes_proporcoes", (*key, variable, record.categoria), record.proporcao, expected_freq.get(record.categoria, -1)/len(valid))
        audit.equal("tecnologias_itens", key, set(actual_tech.tecnologia) == set(TECH), True)
        for record in actual_tech.itertuples(index=False):
            values = frame[TECH[record.tecnologia]]
            n = int(values.notna().sum())
            yes = int(values.eq(True).sum())
            for field, expected in [("denominador", n), ("n", yes if n >= 30 else np.nan), ("proporcao", yes/n if n >= 30 else np.nan)]:
                audit.equal("tecnologias_bases_e_proporcoes", (*key, record.tecnologia, field), getattr(record, field), expected)
    return len(summary)


def main():
    output = AREA / "resultados/auditoria_numerica.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({"status": "EM_EXECUCAO"}), encoding="utf-8")
    package = load_package(DASHBOARD / "dados_publicos")
    sources = {}
    hashes = {}
    for name in ["caged_ti", "state_of_data_brasil"]:
        path = AREA.parent / f"datasets/tratados/{name}.parquet"
        hashes[name] = sha(path)
        if hashes[name] != package["metadata"]["fontes"][name]["sha256"]:
            raise ValueError("Fonte alterada desde a preparacao do pacote: " + name)
        sources[name] = pd.read_parquet(path)
    audit = Audit()
    n_caged = audit_caged(package, sources["caged_ti"], audit)
    print(f"[auditoria] CAGED: {n_caged} recortes conferidos", flush=True)
    n_sod = audit_profiles(package, sources["state_of_data_brasil"], audit)
    report = {"status": "APROVADO" if not audit.n_failures else "FALHOU", "executado_em": datetime.now(timezone.utc).isoformat(),
              "recortes_caged": n_caged, "recortes_state_of_data": n_sod, "comparacoes": dict(audit.checks),
              "total_comparacoes": sum(audit.checks.values()), "n_divergencias": audit.n_failures, "divergencias": audit.failures,
              "tolerancia_numerica": {"absoluta": 1e-7, "relativa": 1e-12}, "fontes_sha256": hashes,
              "manifesto_sha256": sha(DASHBOARD / "dados_publicos/manifesto.json"), "script_sha256": sha(Path(__file__)),
              "escopo": "Conferencia integral dos quatro cubos publicos contra fontes tratadas; nao e auditoria dos microdados originais do MTE nem garantia de representatividade."}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["status", "total_comparacoes", "n_divergencias"]}), flush=True)
    if audit.n_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
