"""Build exact aggregates for the supported UI filters; never pool percentiles."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

AREA = Path(__file__).resolve().parent
NE = {"MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"}
MIN_N = 30
TECH = {"usa_sql": "SQL", "usa_python": "Python", "usa_r": "R", "usa_power_bi": "Power BI", "usa_aws": "AWS", "usa_gcp": "GCP", "usa_azure": "Azure"}
SALARY_ORDER = ["Menos de R$ 1.000/mês", "de R$ 1.001/mês a R$ 2.000/mês", "de R$ 2.001/mês a R$ 3.000/mês",
                "de R$ 3.001/mês a R$ 4.000/mês", "de R$ 4.001/mês a R$ 6.000/mês", "de R$ 6.001/mês a R$ 8.000/mês",
                "de R$ 8.001/mês a R$ 12.000/mês", "de R$ 12.001/mês a R$ 16.000/mês", "de R$ 16.001/mês a R$ 20.000/mês",
                "de R$ 20.001/mês a R$ 25.000/mês", "de R$ 25.001/mês a R$ 30.000/mês", "de R$ 30.001/mês a R$ 40.000/mês", "Acima de R$ 40.001/mês"]


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verified_source(name):
    root = AREA.parent / "datasets"
    report = json.loads((root / "qualidade/execucao_preparacao.json").read_text(encoding="utf-8"))
    relative = f"tratados/{name}.parquet"
    expected = next(p["sha256"] for p in report["produtos"] if p["arquivo"] == relative)
    path = root / relative
    if digest(path) != expected:
        raise ValueError(f"Source changed after preparation: {name}")
    return pd.read_parquet(path), expected


def geographies(frame):
    yield "BR", frame
    yield "NE", frame[frame.uf_sigla.isin(NE)]
    for uf in sorted(frame.uf_sigla.dropna().unique()):
        yield "UF_" + uf, frame[frame.uf_sigla.eq(uf)]


def summarize_caged(frame):
    row = {"n_eventos": len(frame)}
    movements = frame.saldo.to_numpy(dtype=int)
    validity = frame.salario_valido.fillna(False).to_numpy(dtype=bool)
    salaries = frame.salario_real.to_numpy(dtype=float)
    for code, prefix in [(1, "admissoes"), (-1, "desligamentos")]:
        mask = movements == code
        valid = salaries[mask & validity]
        row[prefix] = int(mask.sum())
        row[prefix + "_validos"] = len(valid)
        quantiles = np.quantile(valid, [.1, .5, .9]) if len(valid) >= MIN_N else [np.nan]*3
        for value, label in zip(quantiles, ["p10", "p50", "p90"]):
            row[prefix + "_" + label] = float(value)
    row["diferenca_mov"] = row["admissoes"] - row["desligamentos"]
    return row


def caged_cube(source, catalog):
    records = []
    for geo, region in geographies(source):
        for period in ["2025T1", "202501", "202502", "202503"]:
            frame = region if period == "2025T1" else region[region.competencia.eq(period)]
            area_groups = dict(tuple(frame.groupby("area_ti", observed=True)))
            occupation_groups = dict(tuple(frame.groupby("cbo_codigo", observed=True)))
            empty = frame.iloc[:0]
            for item in catalog:
                selected = frame if item["tipo"] == "total" else (area_groups if item["tipo"] == "area" else occupation_groups).get(item["categoria"], empty)
                records.append({"geo": geo, "periodo": period, **item, **summarize_caged(selected)})
    return pd.DataFrame(records)


def sod_cube(source):
    summaries, distributions, technologies = [], [], []
    for geo, region in geographies(source):
        seniority = region.senioridade_declarada.fillna("Nao informado")
        for senior in ["Todos", "Junior", "Pleno", "Senior", "Nao informado"]:
            by_senior = region if senior == "Todos" else region[seniority.eq(senior)]
            for work in ["Todos", "Remoto", "Hibrido", "Presencial", "Nao informado"]:
                frame = by_senior if work == "Todos" else by_senior[by_senior.modelo_trabalho.eq(work)]
                dims = {"geo": geo, "senioridade": senior, "modelo": work}
                target = frame.planos_mudar_emprego_6m.dropna()
                active = target.str.startswith("Estou em busca de oportunidades").sum()
                summaries.append({**dims, "n_respostas": len(frame), "n_salarios": int(frame.faixa_salarial_declarada.notna().sum()),
                                  "n_alvo": len(target), "n_ativos": int(active) if len(target) >= MIN_N else np.nan,
                                  "proporcao_ativa": float(active/len(target)) if len(target) >= MIN_N else np.nan})
                if len(frame) < MIN_N:
                    continue
                for field, label in [("faixa_salarial_declarada", "salario"), ("nivel_ensino", "formacao"), ("vinculo_grupo", "vinculo")]:
                    valid = frame[field].dropna()
                    if len(valid) < MIN_N:
                        continue
                    counts = valid.astype(str).value_counts()
                    rare = counts[counts < 5]
                    counts = counts[counts >= 5]
                    if len(rare):
                        counts.loc["Outras respostas (categorias pequenas)"] = int(rare.sum())
                    for category, n in counts.items():
                        order = SALARY_ORDER.index(category) if category in SALARY_ORDER else 999
                        distributions.append({**dims, "variavel": label, "categoria": category, "n": int(n),
                                              "denominador": len(valid), "proporcao": n/len(valid), "ordem": order})
                for field, name in TECH.items():
                    values = frame[field]
                    denominator = int(values.notna().sum())
                    yes = int(values.eq(True).sum())
                    technologies.append({**dims, "tecnologia": name, "denominador": denominator,
                                         "n": yes if denominator >= MIN_N else np.nan,
                                         "proporcao": yes/denominator if denominator >= MIN_N else np.nan})
    return pd.DataFrame(summaries), pd.DataFrame(distributions), pd.DataFrame(technologies)


def model_package(out):
    model_meta = {}
    source_hashes = {}
    for phase, kind in [("04_regressao", "regressao"), ("05_classificacao", "classificacao")]:
        root = AREA.parent / phase
        execution = json.loads((root / "registro_execucao.json").read_text(encoding="utf-8"))
        if execution["status"] != "EXECUTADO_SEM_ERROS":
            raise ValueError(f"Unvalidated stage: {phase}")
        paths = (["resultados/tabelas/R1_teste_marco.csv", "resultados/tabelas/R1_ajuste_jan_fev.csv", "resultados/graficos/R3_observado_previsto.png", "resultados/graficos/R4_residuos.png"]
                 if kind == "regressao" else ["resultados/tabelas/C1_metricas_teste.csv", "resultados/tabelas/C4_curvas_roc.csv", "resultados/tabelas/C5_curvas_precision_recall.csv"])
        for relative in paths:
            path = root / relative
            if digest(path) != execution["produtos_sha256"][relative]:
                raise ValueError(f"Model artifact changed: {phase}/{relative}")
            shutil.copy2(path, out / path.name)
        audit = json.loads((root / "resultados/auditoria_modelagem.json").read_text(encoding="utf-8"))
        train_n = int(pd.read_csv(root / "resultados/tabelas/R1_ajuste_jan_fev.csv").iloc[0].n) if kind == "regressao" else audit["n_treino"]
        test_n = int(pd.read_csv(root / "resultados/tabelas/R1_teste_marco.csv").iloc[0].n) if kind == "regressao" else audit["n_teste"]
        model_meta[kind] = {"modelo_selecionado": audit["modelo_escolhido_antes_do_teste"],
                            "n_treino": train_n, "n_teste": test_n,
                            "limiar": audit.get("limiar_fixo"), "fonte_sha256": execution["fonte_sha256"]}
        source_hashes[phase] = digest(root / "registro_execucao.json")
    return model_meta, source_hashes


def main():
    out = AREA / "dados_publicos"
    out.mkdir(exist_ok=True)
    caged, caged_hash = verified_source("caged_ti")
    sod, sod_hash = verified_source("state_of_data_brasil")
    catalog = [{"tipo": "total", "categoria": "Todos", "rotulo": "Todas as ocupacoes", "area": "Todas"}]
    catalog += [{"tipo": "area", "categoria": name, "rotulo": name, "area": name} for name in sorted(caged.area_ti.unique())]
    catalog += [{"tipo": "cargo", "categoria": row.cbo_codigo, "rotulo": row.cbo_nome, "area": row.area_ti}
                for row in caged[["cbo_codigo", "cbo_nome", "area_ti"]].drop_duplicates().sort_values("cbo_codigo").itertuples()]
    print("[pacote] Agregando CAGED com quantis exatos para cada filtro", flush=True)
    caged_cube(caged, catalog).to_parquet(out / "emprego.parquet", index=False)
    print("[pacote] Agregando perfis, faixas e tecnologias", flush=True)
    summary, frequencies, tech = sod_cube(sod)
    for name, frame in [("perfis", summary), ("distribuicoes", frequencies), ("tecnologias", tech)]:
        frame.to_parquet(out / f"{name}.parquet", index=False)
    models, model_hashes = model_package(out)
    ufs = caged[["uf_sigla", "uf_nome"]].drop_duplicates().sort_values("uf_sigla")
    metadata = {"versao": 1, "preparado_em": datetime.now(timezone.utc).isoformat(), "minimo_estatistico": MIN_N,
                "fontes": {"caged_ti": {"sha256": caged_hash, "n": len(caged), "periodo": "Jan-mar/2025"},
                           "state_of_data_brasil": {"sha256": sod_hash, "n": len(sod), "periodo": "2024-2025"}},
                "catalogo": catalog, "ufs": [{"sigla": row.uf_sigla, "nome": row.uf_nome, "nordeste": row.uf_sigla in NE} for row in ufs.itertuples()],
                "modelos": models, "execucoes_modelos_sha256": model_hashes,
                "regra_quantis": "Calculados diretamente dos eventos elegiveis de cada filtro; nunca media de percentis.",
                "privacidade": "Somente agregados de fontes publicas; sem G12, IDs ou previsoes individuais.",
                "publicacao_externa": False,
                "arquivos": {path.name: {"sha256": digest(path), "bytes": path.stat().st_size} for path in sorted(out.iterdir()) if path.is_file() and path.name != "manifesto.json"}}
    (out / "manifesto.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PACOTE_PUBLICO_VALIDADO", "n_arquivos": len(metadata["arquivos"]),
                      "bytes": sum(p["bytes"] for p in metadata["arquivos"].values())}), flush=True)


if __name__ == "__main__":
    main()
