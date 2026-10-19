"""Aggregate correctness, publication safety and Streamlit UI smoke tests."""
from __future__ import annotations

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
from dados import FORBIDDEN, MIN_N, PackageError, caged_query, export_csv, geography, load_package, occupation, profile_query
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


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(AREA / "dashboard.py"), default_timeout=30).run()

    def metric(self, label):
        return next(m.value for m in self.app.metric if m.label == label)

    def test_default_page_is_usable_and_matches_pernambuco(self):
        self.assertFalse(self.app.exception)
        self.assertEqual(self.metric("Mediana de admissão"), "R$ 3.165")
        self.assertEqual(self.metric("Admissões"), "1.284")
        self.assertTrue(self.app.selectbox(key="c_uf").disabled)

    def test_country_filter_updates_metrics(self):
        self.app.selectbox(key="c_regiao").select("Brasil").run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.metric("Admissões"), "61.047")

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
        self.app.session_state["visao"] = "Perfis em dados"
        self.app.run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.metric("Respostas no recorte"), "5.076")
        table = load_package(AREA / "dados_publicos")["perfis"]
        candidate = table[table.geo.str.startswith("UF_") & table.senioridade.eq("Todos") & table.modelo.eq("Todos") & table.n_respostas.between(1, 29)].iloc[0]
        self.app.selectbox(key="p_uf").select(candidate.geo[3:]).run()
        self.assertTrue(any("Dados insuficientes" in w.value for w in self.app.warning))

    def test_regression_page_preserves_negative_prediction_warning(self):
        self.app.session_state["visao"] = "Modelos"
        self.app.run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any("255 previsões negativas" in w.value for w in self.app.warning))

    def test_majority_model_switch_keeps_zero_recall_visible(self):
        self.app.session_state["visao"] = "Modelos"
        self.app.session_state["modelo_visao"] = "Busca ativa"
        self.app.run()
        self.app.selectbox(key="classificador").select("majoritaria").run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.metric("Recall da classe 1"), "0,0%")
        self.assertEqual(self.metric("F1 da classe 1"), "0.000")

    def test_sources_page_discloses_restriction_without_private_results(self):
        self.app.session_state["visao"] = "Fontes"
        self.app.run()
        self.assertFalse(self.app.exception)
        text = " ".join(m.value for m in self.app.markdown)
        self.assertIn("G12 não está publicada", text)
        self.assertNotIn("respondente_id", text)


if __name__ == "__main__":
    unittest.main()
