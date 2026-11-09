"""Rebuild the analysis and public dashboard package for the expanded period."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, confusion_matrix
from sklearn.model_selection import StratifiedKFold

from preparar_pacote import AREA, MIN_N, caged_cube, digest, sod_cube, verified_source

AVD = AREA.parent
sys.path[:0] = [str(AVD / part) for part in ("datasets/scripts", "04_regressao", "05_classificacao")]
import classificacao as classification
import regressao as regression
from expand_public_sources import BATCH, MONTHS, SURVEY_FILE
from prepare_expansion import prepare_survey, slug

EDITIONS = ("2025/2026", "2024/2025")
SENIORITIES = ("Todos", "Junior", "Pleno", "Senior", "Especialista/Staff+", "Nao informado")
MONTH_LABELS = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")
PERIODS = {
    "todos": ("Jan/2025 a Set/2026", MONTHS),
    "2025": ("2025 inteiro", MONTHS[:12]),
    "2025YTD": ("Jan a Set/2025", MONTHS[:9]),
    "2026YTD": ("Jan a Set/2026", MONTHS[12:]),
    "2025T1": ("Jan a Mar/2025", MONTHS[:3]),
    **{m: (f"{MONTH_LABELS[int(m[4:])-1]}/{m[:4]}", [m]) for m in MONTHS},
}


def catalog_for(caged):
    entries = [{"tipo": "total", "categoria": "Todos", "rotulo": "Todas as ocupacoes", "area": "Todas"}]
    entries.extend({"tipo": "area", "categoria": area, "rotulo": area, "area": area}
                   for area in sorted(caged.area_ti.unique()))
    entries.extend({"tipo": "cargo", "categoria": code, "rotulo": name if pd.notna(name) else f"CBO {code}",
                    "area": area} for code, name, area in caged[["cbo_codigo", "cbo_nome", "area_ti"]]
                   .drop_duplicates("cbo_codigo").sort_values("cbo_codigo").itertuples(index=False, name=None))
    return entries


def regression_results(caged):
    sample = caged.loc[caged.saldo.eq(1) & caged.salario_valido].copy()
    fit = sample.loc[sample.competencia.lt("202510")]
    valid = sample.loc[sample.competencia.between("202510", "202512")]
    train = sample.loc[sample.competencia.lt("202601")]
    test = sample.loc[sample.competencia.ge("202601")]
    x_fit, x_valid, x_train, x_test = map(regression.features, (fit, valid, train, test))
    validation, results = [], []
    for index, key in enumerate(regression.ORDER):
        estimator = regression.make_model(key).fit(x_fit, fit.salario_real.to_numpy(dtype=float))
        validation.append({"modelo": key, "ordem": index, **regression.metricas(valid.salario_real, estimator.predict(x_valid))})
    chosen = regression.winner(pd.DataFrame(validation))
    for key in regression.ORDER:
        estimator = regression.make_model(key).fit(x_train, train.salario_real.to_numpy(dtype=float))
        prediction = estimator.predict(x_test)
        results.append({"modelo": key, **regression.metricas(test.salario_real, prediction)})
        if key == chosen:
            observed = test.salario_real.to_numpy(dtype=float)
            diagnostic = test[["competencia"]].assign(observado=observed, previsto=prediction,
                                                       residuo=observed - prediction)
    monthly = diagnostic.groupby("competencia").agg(n=("residuo", "size"),
        observado=("observado", "median"), previsto=("previsto", "median"), residuo=("residuo", "median")).reset_index()
    edges = np.array([-np.inf, -10000., -5000., -2500., -1000., 0., 1000., 2500., 5000., 10000., np.inf])
    bins = pd.cut(diagnostic.residuo, edges, include_lowest=True)
    residuals = bins.value_counts(sort=False).rename_axis("faixa").reset_index(name="n")
    residuals = residuals.loc[residuals.n.ge(MIN_N)].assign(faixa=lambda frame: frame.faixa.astype(str))
    grid = np.arange(0., 30001., 1000.)
    frequency, _, _ = np.histogram2d(diagnostic.observado, diagnostic.previsto, bins=(grid, grid))
    obs, pred = np.nonzero(frequency >= MIN_N)
    dispersion = pd.DataFrame({"observado": grid[obs], "previsto": grid[pred],
                               "n": frequency[obs, pred].astype(int)})
    return {
        "regressao": pd.DataFrame(results), "regressao_validacao": pd.DataFrame(validation),
        "regressao_mensal": monthly, "regressao_residuos": residuals,
        "regressao_dispersao": dispersion,
    }, {"selecionado": chosen, "ajuste_interno": "Jan a Set/2025", "validacao": "Out a Dez/2025",
        "treino": "2025 inteiro", "teste": "Jan a Set/2026", "n_treino": len(train), "n_teste": len(test),
        "entradas": regression.FEATURES}


def classification_results(old, new):
    fields = ["senioridade_declarada", "nivel_ensino", "modelo_trabalho", "experiencia_dados_faixa"]

    def split(source):
        frame = classification.eligible(source)
        features = frame[fields].copy()
        return features.astype(object).where(features.notna(), np.nan), frame.alvo_busca_ativa.to_numpy(dtype=int)

    x_train, y_train = split(old)
    x_test, y_test = split(new)
    validation, results, curves = [], [], []
    folds = StratifiedKFold(5, shuffle=True, random_state=classification.SEED)
    for index, key in enumerate(classification.ORDER):
        scores = []
        for fit, hold in folds.split(x_train, y_train):
            model = classification.make_model(key).fit(x_train.iloc[fit], y_train[fit])
            scores.append(average_precision_score(y_train[hold], classification.positive_probability(model, x_train.iloc[hold])))
        validation.append({"modelo": key, "ordem": index, "ap_media": float(np.mean(scores))})
    chosen = classification.winner(pd.DataFrame(validation))
    for key in classification.ORDER:
        model = classification.make_model(key).fit(x_train, y_train)
        probability = classification.positive_probability(model, x_test)
        results.append({"modelo": key, **classification.metricas(y_test, probability)})
        for threshold in np.linspace(0., 1., 101):
            tn, fp, fn, tp = confusion_matrix(y_test, probability >= threshold, labels=[0, 1]).ravel()
            curves.append({"modelo": key, "limiar": threshold, "fpr": fp / (tn + fp),
                           "recall": tp / (tp + fn), "precisao": tp / (tp + fp) if tp + fp else 1.0})
    return {
        "classificacao": pd.DataFrame(results), "classificacao_validacao": pd.DataFrame(validation),
        "classificacao_curvas": pd.DataFrame(curves),
    }, {"selecionado": chosen, "treino": EDITIONS[1], "teste": EDITIONS[0], "n_treino": len(y_train),
        "n_teste": len(y_test), "entradas": fields, "limiar": classification.THRESHOLD}


def exploratory(caged, sources):
    counts = caged.groupby(["competencia", "saldo"]).size().unstack(fill_value=0).rename(
        columns={1: "admissoes", -1: "desligamentos"}).reset_index()
    counts["movimentacoes"] = counts.admissoes + counts.desligamentos
    comparable = []
    for year in (2025, 2026):
        mask = caged.competencia.between(f"{year}01", f"{year}09")
        group = caged.loc[mask]
        for region, subset in (("Brasil", group), ("Pernambuco", group.loc[group.uf_sigla.eq("PE")])):
            admissions = subset.loc[subset.saldo.eq(1)]
            comparable.append({"ano": year, "recorte": region, "movimentacoes": len(subset),
                               "admissoes": len(admissions), "desligamentos": int(subset.saldo.eq(-1).sum()),
                               "salario_mediano_admissoes": float(admissions.loc[admissions.salario_valido, "salario_real"].median())})
    cohort, profiles, salary_bands, search = [], [], [], []
    admissions = caged.loc[caged.saldo.eq(1) & caged.salario_valido]
    associations = []
    for dimension in ("grau_instrucao", "faixa_etaria", "jornada_grupo", "area_ti"):
        sample = admissions.groupby(dimension, dropna=True).salario_real
        valid = sample.size()
        quantiles = sample.quantile([.1, .5, .9]).unstack().set_axis(["p10", "p50", "p90"], axis=1)
        table = quantiles.join(valid.rename("n")).loc[lambda frame: frame.n.ge(MIN_N)]
        associations.append(table.rename_axis("categoria").reset_index().assign(dimensao=dimension))
    for edition, frame in sources.items():
        target = classification.active_target(frame.planos_mudar_emprego_6m)
        for label, mask in (("Brasil", frame.vive_no_brasil.fillna(False)), ("Pernambuco", frame.uf_sigla.eq("PE").fillna(False))):
            valid = target.loc[mask].dropna()
            cohort.append({"edicao": edition, "recorte": label, "n_respostas": int(mask.sum()),
                           "n_validas_busca": len(valid), "proporcao_busca": float(valid.mean()) if len(valid) >= MIN_N else np.nan})
        beginner = frame.experiencia_dados_faixa.map(slug).isin(
            ["menos_de_1_ano", "de_1_a_2_anos", "nao_tenho_experiencia_na_area_de_dados"])
        for dimension in ("nivel_ensino", "vinculo_grupo", "modelo_trabalho"):
            counts_start = frame.loc[beginner, dimension].value_counts()
            for category, n in counts_start.items():
                if n >= 5:
                    profiles.append({"edicao": edition, "dimensao": dimension, "categoria": category,
                                     "n": int(n), "denominador": int(counts_start.sum())})
        for dimension in ("cargo_atual", "senioridade_declarada", "modelo_trabalho"):
            for category, group in frame.groupby(dimension):
                frequencies = group.faixa_salarial_declarada.value_counts()
                denominator = int(frequencies.sum())
                if denominator >= MIN_N:
                    for band, n in frequencies.items():
                        if n >= 5:
                            salary_bands.append({"edicao": edition, "dimensao": dimension, "categoria": category,
                                                 "faixa": band, "n": int(n), "denominador": denominator})
                valid = target.loc[group.index].dropna()
                if len(valid) >= MIN_N:
                    search.append({"edicao": edition, "dimensao": dimension, "categoria": category,
                                   "n": len(valid), "proporcao_busca": float(valid.mean())})
    return {"eda_movimentacoes": counts, "eda_comparacao_anos": pd.DataFrame(comparable),
            "eda_comparacao_pesquisas": pd.DataFrame(cohort),
            "eda_associacoes_salariais": pd.concat(associations, ignore_index=True),
            "eda_iniciantes": pd.DataFrame(profiles), "eda_faixas_por_perfil": pd.DataFrame(salary_bands),
            "eda_busca_por_perfil": pd.DataFrame(search)}


def main():
    root = AVD / "datasets"
    raw, treated = root / "brutos" / BATCH, root / "tratados" / BATCH
    summary = json.loads((treated / "resumo.json").read_text(encoding="utf-8"))
    manifest_path = raw / "manifesto.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if digest(manifest_path) != summary["manifesto_bruto_sha256"] or digest(raw / SURVEY_FILE) != manifest["arquivos"][SURVEY_FILE]["sha256"]:
        raise ValueError("Expanded source manifest mismatch")
    fields = list(dict.fromkeys([*regression.FEATURES, "idade_valida", "horas_validas", "faixa_etaria", "jornada_grupo",
        "competencia", "saldo", "salario_valido", "salario_real", "area_ti", "cbo_nome"]))
    files = [treated / "caged_ti" / f"{month}.parquet" for month in MONTHS]
    monthly = pd.read_parquet(treated / "controle_caged_mensal.parquet").set_index("competencia")
    parts = []
    for month, path in zip(MONTHS, files):
        part = pd.read_parquet(path, columns=fields)
        if not part.competencia.eq(month).all() or len(part) != monthly.loc[month, "movimentacoes_ti"]:
            raise ValueError(f"CAGED does not reconcile: {month}")
        parts.append(part)
    caged = pd.concat(parts, ignore_index=True)
    if len(caged) != summary["caged_total"]:
        raise ValueError("Expanded CAGED total does not reconcile")
    old, old_hash = verified_source("state_of_data_brasil")
    prepare_survey(raw, treated)
    new_path = treated / "state_of_data_brasil_2025_2026.parquet"
    new = pd.read_parquet(new_path)
    if len(new) != summary["state_of_data"]["respostas_brasil"] or not new.vive_no_brasil.all():
        raise ValueError("Expanded survey total does not reconcile")
    new.loc[new.faixa_salarial_invalida, "faixa_salarial_declarada"] = pd.NA
    if not set(old.respondente_id).isdisjoint(new.respondente_id):
        raise ValueError("Survey identifiers overlap")
    sources = {EDITIONS[0]: new, EDITIONS[1]: old}
    print("[1/4] Exploracao e cortes comparaveis", flush=True)
    tables = exploratory(caged, sources)
    print("[2/4] Regressao temporal e classificacao entre edicoes", flush=True)
    for key, (result, metadata) in (
        ("regressao", regression_results(caged)), ("classificacao", classification_results(old, new)),
    ):
        tables.update(result)
        if key == "regressao":
            models = {key: metadata}
        else:
            models[key] = metadata
    print("[3/4] Agregados do painel", flush=True)
    catalog = catalog_for(caged)
    tables["emprego"] = caged_cube(caged, catalog, {key: months for key, (_, months) in PERIODS.items()})
    survey_cubes = [tuple(frame.assign(edicao=edition) for frame in sod_cube(source, SENIORITIES))
                    for edition, source in sources.items()]
    for name, frames in zip(("perfis", "distribuicoes", "tecnologias"), zip(*survey_cubes)):
        tables[name] = pd.concat(frames, ignore_index=True)
    historic = json.loads((AREA / "dados_publicos/manifesto.json").read_text(encoding="utf-8"))
    meta = {
        "versao": 2, "preparado_em": datetime.now(timezone.utc).isoformat(), "minimo_estatistico": MIN_N,
        "catalogo": catalog, "ufs": historic["ufs"], "modelos": models,
        "periodos": {key: {"rotulo": label, "meses": months} for key, (label, months) in PERIODS.items()},
        "edicoes": {edition: {"n": len(frame), "coleta": "out-dez/2025" if edition == EDITIONS[0] else "out-dez/2024"}
                    for edition, frame in sources.items()},
        "fontes": {"caged_ti": {"n": len(caged), "periodo": "Jan/2025 a Set/2026", "ipca_referencia": "202503",
                               "manifesto_sha256": digest(manifest_path),
                               "particoes_sha256": {path.name: digest(path) for path in files}},
                   "state_of_data_2024_2025": {"n": len(old), "sha256": old_hash},
                   "state_of_data_2025_2026": {"n": len(new), "sha256": digest(new_path)}},
    }
    print("[4/4] Exportando pacote publico sem microdados", flush=True)
    out = AREA / "dados_ampliados"
    out.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix=".radar-build-", dir=AREA) as temporary:
        stage = Path(temporary)
        for name, frame in tables.items():
            frame.to_parquet(stage / f"{name}.parquet", index=False)
        meta["arquivos"] = {path.name: {"sha256": digest(path), "bytes": path.stat().st_size} for path in sorted(stage.iterdir())}
        (stage / "manifesto.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        for name in [*meta["arquivos"], "manifesto.json"]:
            (stage / name).replace(out / name)
    print(f"[ok] {sum(item['bytes'] for item in meta['arquivos'].values()):,} bytes", flush=True)


if __name__ == "__main__":
    main()
