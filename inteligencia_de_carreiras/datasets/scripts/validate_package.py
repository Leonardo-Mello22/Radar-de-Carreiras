"""Read exported files and reconcile the package against the original sources."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from prepare_grupo12 import validate_group12
from prepare_datasets import nullable_boolean


def exported_parquets(root: Path):
    return sorted(path for folder in ("tratados", "auxiliares", "agregados", "modelagem", "qualidade")
                  for path in (root / folder).rglob("*.parquet"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    root = parser.parse_args().output
    report = json.loads((root / "qualidade" / "relatorio_qualidade.json").read_text(encoding="utf-8"))
    checks = []
    for path in exported_parquets(root):
        frame = pd.read_parquet(path)
        csv = pd.read_csv(path.with_suffix(".csv"), dtype=str, keep_default_na=False, encoding="utf-8-sig")
        assert csv.shape == frame.shape, path.name
        assert list(csv.columns) == list(frame.columns), path.name
        assert frame.columns.is_unique, path.name
        assert frame.to_csv(index=False, lineterminator="\n") == path.with_suffix(".csv").read_text(encoding="utf-8-sig"), path.name
        checks.append(f"CSV e Parquet conciliados em valores: {path.stem} ({len(frame)} linhas)")
    manifest = json.loads((root / "fontes_manifesto.json").read_text(encoding="utf-8"))
    for source in manifest["arquivos_brutos"]:
        path = root / "brutos" / source["arquivo"]
        with path.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == source["sha256"], path.name
    checks.append("SHA-256 conferido para todas as fontes brutas")
    caged = pd.read_parquet(root / "tratados" / "caged_ti.parquet")
    assert len(caged) == sum(r["movimentacoes_ti"] for r in report["caged"]["controles_mensais"])
    assert caged.registro_id.is_unique
    assert (caged.saldo.eq(1) == caged.movimento.eq("admiss\u00e3o")).all()
    assert (caged.saldo.eq(-1) == caged.movimento.eq("desligamento")).all()
    assert caged.cbo_nome.notna().all() and caged.municipio_nome.notna().all()
    assert caged.area_ti.ne("TI - a classificar").all()
    checks.append("Contagens mensais, movimentos, CBO e municipios reconciliados")
    aggregate = pd.read_parquet(root / "agregados" / "caged_indicadores_uf_area_mes.parquet")
    assert aggregate.movimentacoes.sum() == len(caged)
    assert aggregate.registros_salario_valido.sum() == int(caged.salario_valido.sum())
    assert aggregate.loc[aggregate.registros_salario_valido.lt(30), "salario_real_p50"].isna().all()
    for uf, month, area in [("PE", "202501", "Desenvolvimento de software"), ("SP", "202503", "Dados e bancos de dados")]:
        source = caged[caged.uf_sigla.eq(uf) & caged.competencia.eq(month) & caged.area_ti.eq(area)
                       & caged.movimento.eq("admiss\u00e3o") & caged.salario_valido]
        row = aggregate[aggregate.uf_sigla.eq(uf) & aggregate.competencia.eq(month) & aggregate.area_ti.eq(area)
                        & aggregate.movimento.eq("admiss\u00e3o")].iloc[0]
        if len(source) >= 30:
            assert np.isclose(source.salario_real.median(), row.salario_real_p50)
    checks.append("Agregados, mediana por recorte e bloqueio salarial para n<30 conferidos")
    factors = pd.read_parquet(root / "auxiliares" / "ipca_deflatores.parquet").set_index("competencia").fator_marco_2025
    sample = caged.sample(200, random_state=12)
    expected = sample.salario_nominal.astype(float) * sample.competencia.map(factors)
    np.testing.assert_allclose(sample.salario_real.astype(float), expected)
    features = pd.read_parquet(root / "modelagem" / "caged_features_numericas.parquet")
    for column in ["salario_real", "idade", "horas_contratuais"]:
        assert abs(features[f"{column}_zscore"].mean()) < 1e-8
        assert np.isclose(features[f"{column}_zscore"].std(ddof=0), 1)
        assert features[f"{column}_minmax"].dropna().between(0, 1).all()
    checks.append("Deflacao IPCA e escalas z-score/min-max conferidas")
    with zipfile.ZipFile(root / "brutos" / "state_of_data_2024_2025.zip") as archive:
        source = pd.read_csv(archive.open(next(n for n in archive.namelist() if n.endswith(".csv"))))
    survey = pd.read_parquet(root / "tratados" / "state_of_data_carreiras.parquet")
    assert len(survey) == len(source.drop_duplicates())
    original_rows = survey.respondente_id.str.split(":").str[-1].astype(int) - 2
    expected_age = source.loc[original_rows, "1.a_idade"].reset_index(drop=True)
    pd.testing.assert_series_equal(survey.idade.reset_index(drop=True).astype(float), expected_age.astype(float), check_names=False)
    salary_source = source.loc[original_rows, "2.h_faixa_salarial"].fillna("").to_list()
    assert survey.faixa_salarial_declarada.fillna("").to_list() == salary_source
    expected_manager = nullable_boolean(source.loc[original_rows, "2.d_atua_como_gestor"]).reset_index(drop=True)
    pd.testing.assert_series_equal(survey.atua_como_gestor.reset_index(drop=True), expected_manager, check_names=False)
    manager_without_role = survey.atua_como_gestor.eq(True).fillna(False) & survey.cargo_atual.isna()
    assert survey.loc[manager_without_role, "area_profissional"].eq("Gestao").all()
    checks.append("Indicador booleano de gestao e categoria profissional reconciliados com a fonte")
    above = survey.faixa_salarial_declarada.str.startswith("Acima").fillna(False)
    assert survey.loc[above, "faixa_salario_limite_superior"].isna().all()
    assert survey.loc[above, "faixa_limite_inferior_exclusivo"].eq(True).all()
    assert not any(c in survey.columns for c in ("salario_exato", "salario_estimado"))
    for stem, mask in [("state_of_data_pernambuco", survey.uf_sigla.eq("PE")),
                       ("state_of_data_nordeste", survey.uf_sigla.isin(["MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"]))]:
        assert len(pd.read_parquet(root / "tratados" / f"{stem}.parquet")) == int(mask.sum())
    checks.append("Survey reconciliada com a origem, faixas salariais preservadas e recortes conferidos")
    if (root / "fontes_pesquisa_grupo12.json").exists():
        checks.extend(validate_group12(root))
    result = {"status": "APROVADO_COM_ALERTAS_PESQUISA" if (root / "fontes_pesquisa_grupo12.json").exists() else "APROVADO",
              "verificacoes": checks, "registros_caged": len(caged), "respondentes_survey": len(survey)}
    (root / "qualidade" / "validacao_exports.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2), flush=True)


if __name__ == "__main__":
    main()
