"""Focused regression rules and end-to-end artifact checks."""
from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

import nbformat
import numpy as np
import pandas as pd
from PIL import Image

AREA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AREA))
from regressao import FEATURES, MIN_N, digest, features, make_model, metricas, temporal_split, winner


def sample():
    return pd.DataFrame({"idade": [20, 40, 60], "idade_valida": [True, True, True],
                         "horas_contratuais": [40., 44., 36.], "horas_validas": [True, True, True],
                         "cbo_codigo": ["317110"] * 3, "uf_sigla": ["PE", "SP", "PE"],
                         "grau_instrucao": ["Medio", "Superior", "Medio"]})


class RuleTests(unittest.TestCase):
    def test_features_are_an_allowlist_and_preserve_source(self):
        source = sample().assign(salario_real=9999, salario_nominal=8888, salario_fixo_declarado=7777,
                                 faixa_salario_real="Acima de 15000", registro_id="id", arquivo_origem="origem")
        original = source.copy(deep=True)
        x = features(source)
        self.assertEqual(list(x.columns), FEATURES)
        self.assertFalse(any("salario" in name for name in x.columns))
        pd.testing.assert_frame_equal(source, original)

    def test_invalid_numeric_values_become_missing_not_deleted(self):
        source = sample()
        source.loc[0, ["idade", "idade_valida"]] = [999, False]
        source.loc[1, ["horas_contratuais", "horas_validas"]] = [999, False]
        x = features(source)
        self.assertTrue(np.isnan(x.loc[0, "idade"]))
        self.assertTrue(np.isnan(x.loc[1, "horas_contratuais"]))
        self.assertEqual(len(x), len(source))

    def test_imputation_and_scale_are_fitted_only_on_training(self):
        x = features(sample())
        x.loc[2, "horas_contratuais"] = np.nan
        model = make_model("multipla").fit(x, [2000., 4000., 5000.])
        prep = model.named_steps["preparar"].named_transformers_["numericas"]
        medians = prep.named_steps["imputar"].statistics_.copy()
        means = prep.named_steps["escala"].mean_.copy()
        test = x.iloc[[0]].copy()
        test.loc[:, "idade"] = 1000.
        test.loc[:, "horas_contratuais"] = np.nan
        model.predict(test)
        np.testing.assert_allclose(medians, [40., 42.])
        np.testing.assert_array_equal(prep.named_steps["imputar"].statistics_, medians)
        np.testing.assert_array_equal(prep.named_steps["escala"].mean_, means)

    def test_unknown_categories_are_not_fitted_from_test(self):
        x = features(sample())
        model = make_model("multipla").fit(x, [2000., 4000., 5000.])
        encoder = model.named_steps["preparar"].named_transformers_["categoricas"].named_steps["codificar"]
        before = [list(c) for c in encoder.categories_]
        test = x.iloc[[0]].copy()
        test.loc[:, "uf_sigla"] = "ZZ"
        self.assertTrue(np.isfinite(model.predict(test)).all())
        self.assertEqual([list(c) for c in encoder.categories_], before)
        self.assertNotIn("ZZ", encoder.categories_[1])

    def test_baseline_uses_training_median_only(self):
        x = features(sample())
        model = make_model("mediana").fit(x, [1000., 2000., 9000.])
        np.testing.assert_array_equal(model.predict(x), [2000., 2000., 2000.])

    def test_temporal_partitions_do_not_overlap(self):
        frame = pd.DataFrame({"competencia": ["202501", "202502", "202503"], "registro_id": ["a", "b", "c"]})
        train, test = temporal_split(frame)
        self.assertEqual(set(train.competencia), {"202501", "202502"})
        self.assertEqual(set(test.competencia), {"202503"})
        self.assertFalse(set(train.registro_id) & set(test.registro_id))

    def test_unexpected_month_or_duplicate_identifier_fails(self):
        frame = pd.DataFrame({"competencia": ["202501", "202502", "202503"], "registro_id": ["a", "b", "c"]})
        with self.assertRaises(ValueError):
            temporal_split(frame.assign(competencia=["202501", "202502", "202504"]))
        with self.assertRaises(ValueError):
            temporal_split(frame.assign(registro_id=["a", "a", "c"]))

    def test_metrics_use_observed_minus_predicted_without_clipping(self):
        values = metricas([10, 20], [-10, 10])
        self.assertEqual(values["mae"], 15.)
        self.assertEqual(values["residuo_medio"], 15.)
        self.assertEqual(values["previsoes_negativas"], 1)
        self.assertAlmostEqual(values["rmse"], np.sqrt(250))
        with self.assertRaises(ValueError):
            metricas([10], [np.nan])

    def test_winner_is_selected_from_validation_and_ties_are_stable(self):
        validation = pd.DataFrame({"modelo": ["mediana", "idade", "multipla"], "ordem": [0, 1, 2], "mae": [10., 8., 8.]})
        self.assertEqual(winner(validation), "idade")
        self.assertEqual(winner(validation.assign(mae=10.)), "mediana")


class ExecutedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((AREA / "registro_execucao.json").read_text(encoding="utf-8"))
        cls.audit = json.loads((AREA / "resultados/auditoria_modelagem.json").read_text(encoding="utf-8"))
        cls.pred = pd.read_parquet(AREA / "resultados_locais/previsoes_marco.parquet")

    def test_execution_record_matches_all_current_products(self):
        self.assertEqual(self.report["status"], "EXECUTADO_SEM_ERROS")
        for name, expected in self.report["codigo_sha256"].items():
            self.assertEqual(digest(AREA / name), expected)
        for name, expected in self.report["produtos_sha256"].items():
            self.assertEqual(digest(AREA / name), expected, name)
        self.assertEqual(digest(AREA / "regressao_salarial.ipynb"), self.report["notebook_fonte_sha256"])
        self.assertEqual(digest(AREA.parent / "datasets/tratados/caged_ti.parquet"), self.report["fonte_sha256"])

    def test_source_notebook_is_clean_and_executed_copy_has_no_errors(self):
        clean = nbformat.read(AREA / "regressao_salarial.ipynb", as_version=4)
        executed = nbformat.read(AREA / "resultados/regressao_salarial_executada.ipynb", as_version=4)
        self.assertTrue(all(not c.outputs and c.execution_count is None for c in clean.cells if c.cell_type == "code"))
        code = [c for c in executed.cells if c.cell_type == "code"]
        self.assertEqual(len(code), self.report["celulas_executadas"])
        self.assertTrue(all(c.execution_count is not None for c in code))
        self.assertFalse(any(o.output_type == "error" for c in code for o in c.outputs))
        self.assertEqual(sum("image/png" in o.get("data", {}) for c in code for o in c.outputs), 6)

    def test_all_test_rows_are_march_and_residuals_reconcile(self):
        self.assertEqual(len(self.pred), 19825)
        self.assertEqual(set(self.pred.competencia), {"202503"})
        self.assertFalse(self.pred.registro_id.duplicated().any())
        metrics = pd.read_csv(AREA / "resultados/tabelas/R1_teste_marco.csv")
        for row in metrics.itertuples():
            np.testing.assert_allclose(self.pred[f"residuo_{row.modelo}"], self.pred.salario_observado - self.pred[f"previsto_{row.modelo}"])
            fresh = metricas(self.pred.salario_observado, self.pred[f"previsto_{row.modelo}"])
            self.assertAlmostEqual(fresh["mae"], row.mae, places=6)
            self.assertAlmostEqual(fresh["rmse"], row.rmse, places=6)

    def test_selection_agrees_with_february_and_not_test_sorting(self):
        validation = pd.read_csv(AREA / "resultados/tabelas/R1_validacao_fevereiro.csv")
        self.assertEqual(winner(validation), self.audit["modelo_escolhido_antes_do_teste"])
        self.assertEqual(self.audit["entradas"], FEATURES)
        self.assertEqual(self.audit["treino"], ["202501", "202502"])
        self.assertEqual(self.audit["teste"], ["202503"])

    def test_subgroup_metrics_are_suppressed_below_threshold(self):
        table = pd.read_csv(AREA / "resultados/tabelas/R6_metricas_recortes.csv")
        self.assertTrue(table.loc[table.n < MIN_N, "mae"].isna().all())
        self.assertTrue(table.loc[table.n >= MIN_N, "mae"].notna().all())
        for model, rows in table[table.dimensao.eq("uf_sigla")].groupby("modelo"):
            self.assertEqual(rows.n.sum(), len(self.pred), model)

    def test_sensitivity_keeps_entire_test_in_main_evaluation(self):
        table = pd.read_csv(AREA / "resultados/tabelas/R8_sensibilidade_cauda.csv")
        for _, rows in table.groupby("modelo"):
            self.assertEqual(int(rows.iloc[0].n), len(self.pred))
            self.assertEqual(int(rows.iloc[1:].n.sum()), len(self.pred))

    def test_public_csvs_do_not_contain_row_identifiers(self):
        for path in (AREA / "resultados/tabelas").glob("*.csv"):
            columns = set(pd.read_csv(path, nrows=0).columns)
            self.assertNotIn("registro_id", columns, path.name)
            self.assertNotIn("respondente_id", columns, path.name)

    def test_six_graphs_are_nonblank_and_html_embeds_them(self):
        graphs = list((AREA / "resultados/graficos").glob("*.png"))
        self.assertEqual(len(graphs), 6)
        for path in graphs:
            with Image.open(path) as image:
                self.assertGreater(image.width, 1000)
                pixels = np.asarray(image.convert("RGB"))
                self.assertGreater(float(pixels.std()), 8., path.name)
                self.assertGreater(float((pixels.min(axis=2) < 230).mean()), .015, path.name)
        html = (AREA / "resultados/regressao_salarial.html").read_text(encoding="utf-8")
        class EmbeddedImages(HTMLParser):
            def __init__(self):
                super().__init__()
                self.sources = []

            def handle_starttag(self, tag, attrs):
                if tag == "img":
                    self.sources.append(dict(attrs).get("src", ""))

        parser = EmbeddedImages()
        parser.feed(html)
        self.assertEqual(sum(src.startswith("data:image/png;base64,") for src in parser.sources), 6)


if __name__ == "__main__":
    unittest.main()
