"""Regression tests for navigation, selection context and package validation."""
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
DASHBOARD = AREA.parent / "06_dashboard_e_publicacao"
sys.path.insert(0, str(DASHBOARD))
sys.path.insert(0, str(AREA))
from dados import PackageError, caged_groups, caged_query, load_package
from auditar_numeros import Audit, grouped_frequencies, salary_statistics

logging.disable(logging.CRITICAL)


class ConsolidationTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(DASHBOARD / "dashboard.py"), default_timeout=30).run()

    def view(self, value):
        self.app.session_state["visao"] = value
        self.app.run()
        self.assertFalse(self.app.exception)

    def captions(self):
        return " ".join(c.value for c in self.app.caption)

    def test_caged_filters_survive_navigation(self):
        self.app.selectbox(key="c_regiao").select("Brasil").run()
        self.app.selectbox(key="c_uf").select("SP").run()
        self.app.selectbox(key="c_periodo").select("202502").run()
        self.app.selectbox(key="c_cargo").select("212405").run()
        before = [m.value for m in self.app.metric]
        self.view("Fontes")
        self.view("Emprego formal")
        self.assertEqual(self.app.selectbox(key="c_uf").value, "SP")
        self.assertEqual(self.app.selectbox(key="c_periodo").value, "202502")
        self.assertEqual(self.app.selectbox(key="c_cargo").value, "212405")
        self.assertEqual([m.value for m in self.app.metric], before)

    def test_profile_filters_survive_navigation(self):
        self.view("Perfis em dados")
        self.app.selectbox(key="p_senior").select("Junior").run()
        self.app.selectbox(key="p_modelo").select("Remoto").run()
        before = [m.value for m in self.app.metric]
        self.view("Emprego formal")
        self.view("Perfis em dados")
        self.assertEqual(self.app.selectbox(key="p_senior").value, "Junior")
        self.assertEqual(self.app.selectbox(key="p_modelo").value, "Remoto")
        self.assertEqual([m.value for m in self.app.metric], before)

    def test_model_selection_survives_navigation(self):
        self.app.session_state["modelo_visao"] = "Busca ativa"
        self.view("Modelos")
        self.app.selectbox(key="classificador").select("arvore").run()
        before = [m.value for m in self.app.metric]
        self.view("Fontes")
        self.view("Modelos")
        self.assertEqual(self.app.selectbox(key="classificador").value, "arvore")
        self.assertEqual([m.value for m in self.app.metric], before)

    def test_active_occupation_is_visible_outside_filter_panel(self):
        self.app.selectbox(key="c_cargo").select("212405").run()
        self.assertIn("CBO 212405", self.captions())
        self.assertIn("Área:", self.captions())

    def test_active_profile_context_is_visible(self):
        self.view("Perfis em dados")
        self.app.selectbox(key="p_senior").select("Junior").run()
        self.app.selectbox(key="p_modelo").select("Hibrido").run()
        self.assertIn("Senioridade: Júnior · Trabalho: Híbrido", self.captions())

    def test_empty_profile_retains_context_and_can_be_reset(self):
        self.view("Perfis em dados")
        self.app.selectbox(key="p_uf").select("AC").run()
        self.assertTrue(any("Nenhuma resposta" in i.value for i in self.app.info))
        self.assertTrue(any(h.value == "AC" for h in self.app.subheader))
        self.assertEqual(len(self.app.metric), 0)
        self.app.button(key="reset_profiles").click().run()
        self.assertEqual(self.app.metric[0].value, "5.076")

    def test_reset_caged_does_not_erase_profile_filters(self):
        self.view("Perfis em dados")
        self.app.selectbox(key="p_modelo").select("Remoto").run()
        self.view("Emprego formal")
        self.app.button(key="reset_caged").click().run()
        self.view("Perfis em dados")
        self.assertEqual(self.app.selectbox(key="p_modelo").value, "Remoto")

    def test_reset_profile_defaults_survive_navigation(self):
        self.view("Perfis em dados")
        self.app.selectbox(key="p_senior").select("Junior").run()
        self.app.selectbox(key="p_modelo").select("Remoto").run()
        self.app.button(key="reset_profiles").click().run()
        self.assertEqual(self.app.selectbox(key="p_senior").value, "Todos")
        self.assertEqual(self.app.selectbox(key="p_modelo").value, "Todos")
        self.view("Modelos")
        self.view("Perfis em dados")
        self.assertEqual(self.app.selectbox(key="p_senior").value, "Todos")
        self.assertEqual(self.app.selectbox(key="p_modelo").value, "Todos")
        self.assertEqual(self.app.metric[0].value, "5.076")

    def test_profile_item_specific_insufficiency_is_explicit(self):
        table = load_package(DASHBOARD / "dados_publicos")["perfis"]
        row = table[table.n_respostas.ge(30) & table.n_alvo.lt(30)].iloc[0]
        self.app.session_state["p_regiao"] = "Brasil"
        self.app.session_state["p_uf"] = row.geo[3:] if row.geo.startswith("UF_") else "Todas"
        self.app.session_state["p_senior"] = row.senioridade
        self.app.session_state["p_modelo"] = row.modelo
        self.view("Perfis em dados")
        self.assertTrue(any("Busca ativa indisponível" in w.value for w in self.app.warning))

    def test_independent_sessions_do_not_share_filters(self):
        self.app.selectbox(key="c_regiao").select("Brasil").run()
        other = AppTest.from_file(str(DASHBOARD / "dashboard.py"), default_timeout=30).run()
        self.assertEqual(other.selectbox(key="c_regiao").value, "Pernambuco")
        self.assertEqual(other.metric[1].value, "1.284")

    def test_empty_caged_has_context_without_stale_metrics(self):
        table = load_package(DASHBOARD / "dados_publicos")["emprego"]
        row = table[table.geo.str.startswith("UF_") & table.tipo.eq("cargo") & table.n_eventos.eq(0)].iloc[0]
        self.app.selectbox(key="c_regiao").select("Brasil").run()
        self.app.selectbox(key="c_uf").select(row.geo[3:]).run()
        self.app.selectbox(key="c_periodo").select(row.periodo).run()
        self.app.selectbox(key="c_cargo").select(row.categoria).run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any("Nenhuma movimentação" in i.value for i in self.app.info))
        self.assertIn("CBO " + row.categoria, self.captions())
        self.assertEqual(len(self.app.metric), 0)
        self.app.button(key="reset_caged").click().run()
        self.assertEqual(self.app.metric[1].value, "1.284")

    def test_insufficient_salary_does_not_hide_event_counts(self):
        table = load_package(DASHBOARD / "dados_publicos")["emprego"]
        row = table[table.geo.eq("BR") & table.tipo.eq("cargo") & table.n_eventos.gt(0) & table.admissoes_validos.lt(30)].iloc[0]
        self.app.selectbox(key="c_regiao").select("Brasil").run()
        self.app.selectbox(key="c_periodo").select(row.periodo).run()
        self.app.selectbox(key="c_cargo").select(row.categoria).run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[0].value, "Indisponível")
        self.assertEqual(self.app.metric[1].value, f"{row.admissoes:,}".replace(",", "."))
        self.assertTrue(any("Dados salariais insuficientes" in w.value for w in self.app.warning))


class IntegrityAndAuditTests(unittest.TestCase):
    def test_occupation_chart_uses_occupation_rows_even_with_all_areas(self):
        package = load_package(DASHBOARD / "dados_publicos")
        groups = caged_groups(package, "UF_SP", "202502", "Todas", "212405")
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups.iloc[0].tipo, "cargo")
        self.assertGreaterEqual(groups.iloc[0].admissoes_validos, 30)
        expected = caged_query(package, "UF_SP", "202502", "cargo", "212405")
        pd.testing.assert_frame_equal(groups, expected)
        self.assertEqual(set(caged_groups(package, "BR", "2025T1", "Todas", "Todos").tipo), {"area"})
        area = groups.iloc[0].area
        self.assertEqual(set(caged_groups(package, "BR", "2025T1", area, "Todos").tipo), {"cargo"})

    def test_invalid_manifest_shape_fails_as_package_error(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "manifesto.json").write_text("[]", encoding="utf-8")
            with self.assertRaises(PackageError):
                load_package(directory)

    def test_missing_hash_entry_is_rejected_even_if_file_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "public"
            shutil.copytree(DASHBOARD / "dados_publicos", target)
            path = target / "manifesto.json"
            meta = json.loads(path.read_text(encoding="utf-8"))
            del meta["arquivos"]["emprego.parquet"]
            path.write_text(json.dumps(meta), encoding="utf-8")
            with self.assertRaises(PackageError):
                load_package(target)

    def test_wrong_size_or_statistical_rule_is_rejected(self):
        for change in ["bytes", "minimum"]:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "public"
                shutil.copytree(DASHBOARD / "dados_publicos", target)
                path = target / "manifesto.json"
                meta = json.loads(path.read_text(encoding="utf-8"))
                if change == "bytes":
                    meta["arquivos"]["emprego.parquet"]["bytes"] += 1
                else:
                    meta["minimo_estatistico"] = 1
                path.write_text(json.dumps(meta), encoding="utf-8")
                with self.assertRaises(PackageError):
                    load_package(target)

    def test_independent_statistics_keep_flagged_events_but_not_salary(self):
        source = pd.DataFrame({"saldo": [1]*31 + [-1], "salario_valido": [True]*30 + [False, True],
                               "salario_real": [float(v) for v in range(1000, 1030)] + [999999., 2000.]})
        result = salary_statistics(source)
        self.assertEqual(result["admissoes"], 31)
        self.assertEqual(result["admissoes_validos"], 30)
        self.assertEqual(result["admissoes_p50"], 1014.5)
        self.assertTrue(np.isnan(result["desligamentos_p50"]))

    def test_independent_rare_categories_preserve_total(self):
        frequencies = grouped_frequencies(pd.Series(["A"]*30 + ["B"]*2 + ["C"]*3 + [None]))
        self.assertEqual(frequencies, {"A": 30, "Outras respostas (categorias pequenas)": 5})

    def test_auditor_rejects_divergence_and_missing_instead_of_zero(self):
        audit = Audit()
        audit.equal("sample", "missing", np.nan, np.nan)
        audit.equal("sample", "wrong median", 2000., 2500.)
        audit.equal("sample", "zero instead of missing", 0., np.nan)
        self.assertEqual(audit.n_failures, 2)
        self.assertEqual(audit.checks["sample"], 3)


if __name__ == "__main__":
    unittest.main()
