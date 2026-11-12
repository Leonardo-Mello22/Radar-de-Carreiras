"""Aggregate correctness, publication safety and Streamlit UI smoke tests."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd
os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
from streamlit.testing.v1 import AppTest

AREA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AREA))
from dados import FORBIDDEN, MIN_N, PackageError, caged_query, export_csv, geography, load_expansion, load_package, occupation, profile_query
from preparar_pacote import NE, TECH, summarize_caged

logging.disable(logging.CRITICAL)


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = load_package(AREA / "dados_publicos")
        cls.caged = pd.read_parquet(AREA.parent / "datasets/tratados/caged_ti.parquet")
        cls.sod = pd.read_parquet(AREA.parent / "datasets/tratados/state_of_data_brasil.parquet")

    def test_package_is_small_and_contains_no_individual_fields(self):
        size = sum(v["bytes"] for v in self.package["metadata"]["arquivos"].values())
        self.assertLess(size, 2_000_000)
        for name, value in self.package.items():
            if isinstance(value, pd.DataFrame):
                self.assertFalse(FORBIDDEN.intersection(value.columns), name)

    def test_quarter_quantiles_are_exact_for_filtered_events(self):
        for geo, mask in [("BR", np.ones(len(self.caged), dtype=bool)), ("UF_PE", self.caged.uf_sigla.eq("PE"))]:
            actual = caged_query(self.package, geo, "2025T1").iloc[0]
            expected = summarize_caged(self.caged.loc[mask])
            for field in ["admissoes", "desligamentos", "diferenca_mov", "admissoes_p10", "admissoes_p50", "admissoes_p90"]:
                self.assertAlmostEqual(actual[field], expected[field], places=8, msg=field)

    def test_month_and_occupation_do_not_pool_group_medians(self):
        mask = self.caged.uf_sigla.eq("SP") & self.caged.competencia.eq("202502") & self.caged.cbo_codigo.eq("212405")
        expected = summarize_caged(self.caged[mask])
        actual = caged_query(self.package, "UF_SP", "202502", "cargo", "212405").iloc[0]
        self.assertAlmostEqual(actual.admissoes_p50, expected["admissoes_p50"])
        self.assertEqual(actual.n_eventos, expected["n_eventos"])

    def test_all_small_salary_groups_are_suppressed(self):
        table = self.package["emprego"]
        for prefix in ["admissoes", "desligamentos"]:
            small = table[prefix+"_validos"] < MIN_N
            self.assertTrue(table.loc[small, prefix+"_p50"].isna().all())
            self.assertTrue(table.loc[~small, prefix+"_p50"].notna().all())

    def test_events_include_flagged_salaries(self):
        row = caged_query(self.package, "BR", "2025T1").iloc[0]
        self.assertEqual(row.admissoes, 61047)
        self.assertEqual(row.admissoes_validos, 60862)
        self.assertEqual(row.desligamentos, 57517)
        self.assertEqual(row.diferenca_mov, 3530)

    def test_regional_counts_reconcile_without_nested_double_count(self):
        table = self.package["emprego"]
        total = table[table.periodo.eq("2025T1") & table.tipo.eq("total")]
        self.assertEqual(total[total.geo.str.startswith("UF_")].n_eventos.sum(), 118564)
        northeast = total[total.geo.isin(["UF_"+uf for uf in NE])].n_eventos.sum()
        self.assertEqual(northeast, total[total.geo.eq("NE")].iloc[0].n_eventos)

    def test_profile_missing_target_is_not_a_negative(self):
        result = profile_query(self.package, "BR", "Todos", "Todos")
        row = result["perfis"].iloc[0]
        self.assertEqual(row.n_respostas, 5076)
        self.assertEqual(row.n_alvo, 4734)
        self.assertEqual(row.n_ativos, 1630)
        self.assertAlmostEqual(row.proporcao_ativa, 1630/4734)

    def test_technology_denominators_preserve_item_missing(self):
        tech = profile_query(self.package, "BR", "Todos", "Todos")["tecnologias"].set_index("tecnologia")
        for field, name in TECH.items():
            values = self.sod[field]
            self.assertEqual(tech.loc[name, "denominador"], values.notna().sum())
            self.assertAlmostEqual(tech.loc[name, "proporcao"], values.eq(True).sum()/values.notna().sum())

    def test_distribution_counts_use_question_specific_denominator(self):
        table = profile_query(self.package, "BR", "Todos", "Todos")["distribuicoes"]
        for _, rows in table.groupby("variavel"):
            self.assertEqual(rows.n.sum(), rows.denominador.iloc[0])
            self.assertAlmostEqual(rows.proporcao.sum(), 1.)
        self.assertEqual(table[table.variavel.eq("salario")].denominador.iloc[0], 4734)

    def test_small_profiles_never_include_distributions(self):
        for row in self.package["perfis"].query("n_respostas < 30").head(15).itertuples():
            result = profile_query(self.package, row.geo, row.senioridade, row.modelo)
            self.assertTrue(result["distribuicoes"].empty)
            self.assertTrue(result["tecnologias"].empty)
            self.assertTrue(pd.isna(result["perfis"].iloc[0].proporcao_ativa))

    def test_filter_resolution_is_unambiguous(self):
        self.assertEqual(geography("Pernambuco", "Todas"), "UF_PE")
        self.assertEqual(geography("Nordeste", "Todas"), "NE")
        self.assertEqual(geography("Brasil", "SP"), "UF_SP")
        self.assertEqual(occupation("Todas", "Todos"), ("total", "Todos"))
        self.assertEqual(occupation("Gestao de TI", "Todos"), ("area", "Gestao de TI"))
        self.assertEqual(occupation("Gestao de TI", "123605"), ("cargo", "123605"))

    def test_download_refuses_individual_data(self):
        with self.assertRaises(PackageError):
            export_csv(pd.DataFrame({"respondente_id": ["private"]}))
        self.assertTrue(export_csv(pd.DataFrame({"n": [30]})).startswith(b"\xef\xbb\xbf"))

    def test_deployment_package_works_without_raw_datasets(self):
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(AREA / "dados_publicos", Path(directory) / "dados_publicos")
            package = load_package(Path(directory) / "dados_publicos")
            self.assertEqual(package["metadata"]["versao"], 1)

    def test_tampered_or_missing_package_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PackageError):
                load_package(directory)
            target = Path(directory) / "copy"
            shutil.copytree(AREA / "dados_publicos", target)
            with (target / "emprego.parquet").open("ab") as stream:
                stream.write(b"corrupted")
            with self.assertRaises(PackageError):
                load_package(target)


class ExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = load_expansion(AREA / "dados_ampliados")

    def test_all_months_and_exact_comparable_totals(self):
        expected = {"todos": 842731, "2025": 483006, "2025YTD": 370147, "2026YTD": 359725}
        months = self.package["metadata"]["periodos"]["todos"]["meses"]
        self.assertEqual(len(months), 21)
        for period, total in expected.items():
            self.assertEqual(caged_query(self.package, "BR", period).iloc[0].n_eventos, total)
        self.assertEqual(sum(caged_query(self.package, "BR", month).iloc[0].n_eventos for month in months), expected["todos"])

    def test_expanded_period_quantiles_are_computed_from_events(self):
        root = AREA.parent / "datasets/tratados/atualizacao_2025_2026/caged_ti"
        if not root.is_dir():
            self.skipTest("Local prepared CAGED is unavailable")
        cols = ["saldo", "salario_valido", "salario_real", "uf_sigla", "cbo_codigo"]
        months = self.package["metadata"]["periodos"]["2026YTD"]["meses"]
        sample = pd.concat([pd.read_parquet(root / f"{m}.parquet", columns=cols) for m in months])
        mask = (sample.uf_sigla.eq("PE").fillna(False).to_numpy(dtype=bool)
                & sample.cbo_codigo.eq("212405").fillna(False).to_numpy(dtype=bool))
        expected = summarize_caged(sample.loc[mask])
        actual = caged_query(self.package, "UF_PE", "2026YTD", "cargo", "212405").iloc[0]
        for field in ("n_eventos", "admissoes_p10", "admissoes_p50", "admissoes_p90"):
            self.assertAlmostEqual(actual[field], expected[field], places=8)

    def test_editions_have_separate_denominators(self):
        for edition, n, targets in (("2025/2026", 3372, 3123), ("2024/2025", 5076, 4734)):
            result = profile_query(self.package, "BR", "Todos", "Todos", edition)
            self.assertEqual(result["perfis"].iloc[0].n_respostas, n)
            self.assertEqual(result["perfis"].iloc[0].n_alvo, targets)
            self.assertTrue(result["tecnologias"].edicao.eq(edition).all())
            self.assertTrue(result["tecnologias"].denominador.between(30, n).all())

    def test_package_is_compact_and_contains_only_aggregates(self):
        size = sum(item["bytes"] for item in self.package["metadata"]["arquivos"].values())
        self.assertLess(size, 2_000_000)
        for frame in self.package.values():
            if isinstance(frame, pd.DataFrame):
                self.assertFalse(FORBIDDEN.intersection(frame.columns))
        for prefix in ("admissoes", "desligamentos"):
            frame = self.package["emprego"]
            self.assertTrue(frame.loc[frame[prefix+"_validos"].lt(MIN_N), prefix+"_p50"].isna().all())

    def test_model_diagnostics_match_reserved_test_sizes(self):
        meta = self.package["metadata"]["modelos"]
        for name, n in (("regressao", 182057), ("classificacao", 3123)):
            table = self.package[name]
            self.assertTrue(table.n.eq(n).all())
            self.assertEqual(meta[name]["n_teste"], n)
            self.assertIn(meta[name]["selecionado"], set(table.modelo))
        cls = self.package["classificacao"]
        self.assertTrue((cls[["tn", "fp", "fn", "tp"]].sum(axis=1) == cls.n).all())


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(AREA / "dashboard.py"), default_timeout=30).run()

    def metric(self, label):
        return next(m.value for m in self.app.metric if m.label == label)

    def chart_specs(self):
        return [json.loads(item.proto.spec) for item in self.app.get("vega_lite_chart")]

    def test_monthly_charts_show_all_groups_without_blue_points(self):
        ranges, movements, salary = self.chart_specs()
        self.assertFalse(ranges["layer"][0]["encoding"]["y"]["axis"]["labelOverlap"])
        self.assertEqual(len(movements["encoding"]["y"]["sort"]), 21)
        self.assertEqual(movements["encoding"]["yOffset"]["field"], "movimento")
        self.assertGreaterEqual(movements["height"], 21 * 30)
        self.assertEqual(salary["mark"]["type"], "line")
        self.assertFalse(salary["mark"]["point"])
        self.app.selectbox(key="c_periodo").select("202501").run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.chart_specs()[-1]["mark"]["type"], "point")

    def test_profile_education_uses_short_ordered_labels_in_both_editions(self):
        self.app.button(key="navtab_1").click().run()
        expected = ["Sem graduação", "Graduando", "Graduação", "Especialização",
                    "Mestrado", "Doutorado", "Não informado"]
        for edition in ("2025/2026", "2024/2025"):
            with self.subTest(edition=edition):
                self.app.selectbox(key="p_edicao").select(edition).run()
                self.assertFalse(self.app.exception)
                education = self.chart_specs()[2]
                self.assertEqual(education["encoding"]["y"]["sort"], expected)
                self.assertFalse(education["encoding"]["y"]["axis"]["labelOverlap"])
                self.assertIn("Especialização", education["encoding"]["color"]["condition"]["test"])

    def test_default_page_is_usable_and_matches_pernambuco(self):
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.selectbox(key="c_periodo").value, "todos")
        self.assertGreater(int(self.metric("Contratações").replace(".", "")), 1284)
        self.assertTrue(self.app.selectbox(key="c_uf").disabled)

    def test_country_filter_updates_metrics(self):
        self.app.selectbox(key="c_regiao").select("Brasil").run()
        self.assertFalse(self.app.exception)
        self.app.selectbox(key="c_periodo").select("2025T1").run()
        self.assertEqual(self.metric("Contratações"), "61.047")
        self.app.selectbox(key="c_periodo").select("202609").run()
        self.assertFalse(self.app.exception)
        self.assertGreater(int(self.metric("Contratações").replace(".", "")), 0)

    def test_region_change_resets_invalid_uf(self):
        self.app.selectbox(key="c_regiao").select("Brasil").run()
        self.app.selectbox(key="c_uf").select("SP").run()
        self.app.selectbox(key="c_regiao").select("Nordeste").run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.selectbox(key="c_uf").value, "Todas")

    def test_area_change_resets_incompatible_occupation(self):
        self.app.selectbox(key="c_cargo").select("212405").run()
        self.app.selectbox(key="c_area").select("Suporte e operacoes").run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.selectbox(key="c_cargo").value, "Todos")

    def test_restore_filters_returns_to_default(self):
        self.app.selectbox(key="c_regiao").select("Brasil").run()
        self.app.button(key="reset_caged").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.selectbox(key="c_regiao").value, "Pernambuco")

    def test_profiles_page_and_small_sample_warning(self):
        self.app.button(key="navtab_1").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.metric("Pessoas que responderam"), "3.372")
        self.app.selectbox(key="p_edicao").select("2024/2025").run()
        self.assertEqual(self.metric("Pessoas que responderam"), "5.076")
        table = load_package(AREA / "dados_publicos")["perfis"]
        candidate = table[table.geo.str.startswith("UF_") & table.senioridade.eq("Todos") & table.modelo.eq("Todos") & table.n_respostas.between(1, 29)].iloc[0]
        self.app.selectbox(key="p_uf").select(candidate.geo[3:]).run()
        self.assertTrue(any("Há poucas respostas" in w.value for w in self.app.warning))

    def test_regression_page_preserves_negative_prediction_warning(self):
        self.app.button(key="navtab_2").click().run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any("estimativas negativas" in w.value for w in self.app.warning))
        self.assertTrue(any("Teste reservado: Jan a Set/2026" in c.value for c in self.app.caption))

    def test_classification_keeps_recall_and_reference_visible(self):
        self.app.session_state["visao"] = "Previsões"
        self.app.session_state["modelo_visao"] = "Quem procura emprego"
        self.app.run()
        self.assertFalse(self.app.exception)
        self.assertLess(float(self.metric("Recall de busca ativa").rstrip("%").replace(",", ".")), 20.)
        self.assertEqual(self.metric("Acurácia da referência"), "65,6%")

    def test_sources_page_discloses_restriction_without_private_results(self):
        self.app.button(key="navtab_4").click().run()
        self.assertFalse(self.app.exception)
        text = " ".join(m.value for m in self.app.markdown)
        self.assertIn("842.731 movimentações", text)
        self.assertIn("somente os resultados agregados da turma", text)
        self.assertNotIn("respondente_id", text)


if __name__ == "__main__":
    unittest.main()
