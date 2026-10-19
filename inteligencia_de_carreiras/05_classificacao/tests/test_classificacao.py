"""Target, leakage, train-only preparation and executed classifier checks."""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import unittest

import nbformat
import numpy as np
import pandas as pd
from PIL import Image

AREA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AREA))
from classificacao import (ACTIVE, FEATURES, MIN_N, THRESHOLD, active_target, digest, eligible, features,
                           labels, make_model, metricas, positive_probability, split_indices, winner)


def profiles():
    return pd.DataFrame({field: ["Categoria A", "Categoria A", "Categoria B", "Categoria B"] for field in FEATURES})


class RuleTests(unittest.TestCase):
    def test_target_mapping_preserves_missing(self):
        target = active_target(pd.Series([*ACTIVE, None]))
        self.assertEqual(target.iloc[:4].tolist(), [1, 1, 0, 0])
        self.assertTrue(pd.isna(target.iloc[4]))

    def test_unknown_target_answer_requires_review(self):
        with self.assertRaises(ValueError):
            active_target(pd.Series(["Resposta nova"]))

    def test_eligibility_does_not_turn_missing_target_into_negative(self):
        frame = pd.DataFrame({"vive_no_brasil": [True, True, False, None],
                              "planos_mudar_emprego_6m": [next(iter(ACTIVE)), None, next(iter(ACTIVE)), None]})
        result = eligible(frame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.alvo_busca_ativa.tolist(), [1])

    def test_feature_allowlist_excludes_target_and_search_proxies(self):
        source = profiles().assign(planos_mudar_emprego_6m="alvo", copia_alvo=1, participou_entrevistas_6m="sim",
                                   oportunidade_buscada="analista", tempo_busca_oportunidade="6 meses",
                                   objetivo_carreira="recolocacao", situacao_trabalho="Desempregado, buscando recolocacao",
                                   satisfeito_trabalho="nao", respondente_id="ID")
        self.assertEqual(list(features(source).columns), FEATURES)
        self.assertNotIn("situacao_trabalho", FEATURES)

    def test_feature_missing_is_preserved_and_source_unchanged(self):
        source = profiles()
        source.loc[0, "senioridade_declarada"] = None
        original = source.copy(deep=True)
        self.assertTrue(pd.isna(features(source).loc[0, "senioridade_declarada"]))
        pd.testing.assert_frame_equal(source, original)

    def test_test_categories_do_not_change_training_encoder(self):
        x = profiles()
        x.loc[0, "senioridade_declarada"] = np.nan
        for key in ["logistica", "arvore"]:
            model = make_model(key).fit(x, [0, 1, 0, 1])
            encoder = model.named_steps["codificar"]
            before = [list(c) for c in encoder.categories_]
            unseen = x.iloc[[0]].copy()
            unseen.loc[:, "nivel_ensino"] = "Categoria nunca vista"
            self.assertTrue(np.isfinite(positive_probability(model, unseen)).all())
            self.assertEqual([list(c) for c in encoder.categories_], before)

    def test_majority_baseline_uses_training_prior(self):
        model = make_model("majoritaria").fit(profiles(), [0, 0, 0, 1])
        p = positive_probability(model, profiles())
        np.testing.assert_allclose(p, .25)
        np.testing.assert_array_equal(labels(p), [0, 0, 0, 0])

    def test_metrics_have_correct_positive_class_and_confusion_orientation(self):
        metrics = metricas([0, 0, 1, 1], [.1, .8, .7, .2])
        self.assertEqual([metrics[k] for k in ["tn", "fp", "fn", "tp"]], [1, 1, 1, 1])
        self.assertEqual(metrics["n_ativos"], 2)
        for field in ["acuracia", "precisao", "recall", "f1", "roc_auc"]:
            self.assertAlmostEqual(metrics[field], .5)

    def test_no_positive_predictions_are_reported_honestly(self):
        metrics = metricas([0, 0, 1, 1], [.2] * 4)
        self.assertEqual(metrics["precisao"], 0.)
        self.assertEqual(metrics["recall"], 0.)
        self.assertEqual(metrics["f1"], 0.)
        self.assertEqual(metrics["roc_auc"], .5)
        self.assertEqual(metrics["average_precision"], .5)

    def test_single_class_subgroups_have_no_auc_or_ap(self):
        metrics = metricas([0, 0], [.2, .3])
        self.assertIsNone(metrics["roc_auc"])
        self.assertIsNone(metrics["average_precision"])

    def test_invalid_probabilities_thresholds_and_targets_fail(self):
        for values in [[np.nan], [-.1], [1.1]]:
            with self.assertRaises(ValueError):
                labels(values)
        with self.assertRaises(ValueError):
            labels([.2], threshold=1.1)
        with self.assertRaises(ValueError):
            metricas([.5], [.2])

    def test_positive_probability_uses_class_order_not_fixed_column(self):
        class ReversedClasses:
            classes_ = np.array([1, 0])

            def predict_proba(self, x):
                return np.array([[.7, .3], [.1, .9]])
        np.testing.assert_allclose(positive_probability(ReversedClasses(), None), [.7, .1])

    def test_stratified_split_is_reproducible_and_disjoint(self):
        frame = pd.DataFrame({"respondente_id": [f"id{i}" for i in range(20)], "alvo_busca_ativa": [0, 1]*10})
        train, test = split_indices(frame)
        repeated_train, repeated_test = split_indices(frame)
        np.testing.assert_array_equal(train, repeated_train)
        np.testing.assert_array_equal(test, repeated_test)
        self.assertFalse(set(train) & set(test))
        self.assertEqual(len(train), 16)
        self.assertEqual(int(frame.iloc[test].alvo_busca_ativa.sum()), 2)

    def test_duplicate_ids_or_single_training_class_are_rejected(self):
        frame = pd.DataFrame({"respondente_id": ["a", "a"], "alvo_busca_ativa": [0, 1]})
        with self.assertRaises(ValueError):
            split_indices(frame)
        with self.assertRaises(ValueError):
            split_indices(frame.assign(respondente_id=["a", "b"], alvo_busca_ativa=0))

    def test_model_selection_uses_training_ap_not_accuracy_or_test(self):
        validation = pd.DataFrame({"modelo": ["majoritaria", "logistica", "arvore"], "ordem": [0, 1, 2],
                                   "ap_media": [.3, .4, .4], "acuracia": [.99, .6, .8]})
        self.assertEqual(winner(validation), "logistica")
        self.assertEqual(winner(validation.assign(ap_media=.3)), "majoritaria")


class ExecutedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((AREA / "registro_execucao.json").read_text(encoding="utf-8"))
        cls.audit = json.loads((AREA / "resultados/auditoria_modelagem.json").read_text(encoding="utf-8"))
        cls.test = pd.read_parquet(AREA / "resultados_locais/previsoes_teste.parquet")
        cls.train = pd.read_parquet(AREA / "resultados_locais/previsoes_oof_treino.parquet")
        cls.metrics = pd.read_csv(AREA / "resultados/tabelas/C1_metricas_teste.csv")

    def test_execution_and_current_product_integrity(self):
        self.assertEqual(self.report["status"], "EXECUTADO_SEM_ERROS")
        for name, sha in self.report["codigo_sha256"].items():
            self.assertEqual(digest(AREA / name), sha)
        for name, sha in self.report["produtos_sha256"].items():
            self.assertEqual(digest(AREA / name), sha, name)
        self.assertEqual(digest(AREA / "classificacao_busca_ativa.ipynb"), self.report["notebook_fonte_sha256"])
        self.assertEqual(digest(AREA.parent / "datasets/tratados/state_of_data_brasil.parquet"), self.report["fonte_sha256"])

    def test_partitions_reconcile_source_and_are_disjoint(self):
        self.assertEqual(len(self.train), 3787)
        self.assertEqual(len(self.test), 947)
        self.assertEqual(int(self.train.alvo_observado.sum()), 1304)
        self.assertEqual(int(self.test.alvo_observado.sum()), 326)
        self.assertFalse(set(self.train.respondente_id) & set(self.test.respondente_id))
        self.assertFalse(self.train.respondente_id.duplicated().any())
        self.assertFalse(self.test.respondente_id.duplicated().any())

    def test_reported_metrics_and_confusion_counts_reconcile(self):
        for row in self.metrics.itertuples():
            actual = metricas(self.test.alvo_observado, self.test[f"probabilidade_{row.modelo}"])
            for field in ["acuracia", "precisao", "recall", "f1", "roc_auc", "average_precision", "tn", "fp", "fn", "tp", "brier"]:
                self.assertAlmostEqual(actual[field], getattr(row, field), places=10)
            np.testing.assert_array_equal(labels(self.test[f"probabilidade_{row.modelo}"]), self.test[f"classe_{row.modelo}"])

    def test_selection_matches_folds_and_threshold_is_fixed(self):
        validation = pd.read_csv(AREA / "resultados/tabelas/C1_selecao_treino.csv")
        folds = pd.read_csv(AREA / "resultados/tabelas/C1_validacao_folds.csv")
        self.assertEqual(winner(validation), self.audit["modelo_escolhido_antes_do_teste"])
        self.assertEqual(self.audit["limiar_fixo"], THRESHOLD)
        self.assertEqual(self.audit["entradas"], FEATURES)
        for row in validation.itertuples():
            current = folds[folds.modelo.eq(row.modelo)]
            self.assertEqual(len(current), 5)
            self.assertEqual(current.n.sum(), len(self.train))
            self.assertAlmostEqual(current.average_precision.mean(), row.ap_media)

    def test_threshold_sensitivity_uses_only_oof_train_predictions(self):
        table = pd.read_csv(AREA / "resultados/tabelas/C6_limiares_oof_treino.csv")
        self.assertTrue(table.n.eq(len(self.train)).all())
        selected = self.audit["modelo_escolhido_antes_do_teste"]
        for row in table.itertuples():
            fresh = metricas(self.train.alvo_observado, self.train[f"probabilidade_oof_{selected}"], row.limiar)
            self.assertAlmostEqual(fresh["f1"], row.f1)

    def test_no_small_group_or_calibration_metrics_are_exposed(self):
        groups = pd.read_csv(AREA / "resultados/tabelas/C8_cobertura_recortes.csv")
        self.assertTrue(groups.loc[groups.n < MIN_N, "acuracia"].isna().all())
        self.assertTrue(groups.loc[groups.n >= MIN_N, "acuracia"].notna().all())
        bins = pd.read_csv(AREA / "resultados/tabelas/C7_calibracao_faixas.csv")
        self.assertEqual(bins.n.sum(), len(self.test))
        self.assertTrue(bins.loc[bins.n < MIN_N, "proporcao_ativa"].isna().all())

    def test_public_tables_have_no_individual_identifiers(self):
        for path in (AREA / "resultados/tabelas").glob("*.csv"):
            columns = set(pd.read_csv(path, nrows=0).columns)
            self.assertNotIn("respondente_id", columns, path.name)
            self.assertNotIn("registro_id", columns, path.name)

    def test_notebook_runs_all_code_and_source_is_clean(self):
        clean = nbformat.read(AREA / "classificacao_busca_ativa.ipynb", as_version=4)
        executed = nbformat.read(AREA / "resultados/classificacao_busca_ativa_executada.ipynb", as_version=4)
        self.assertTrue(all(not c.outputs and c.execution_count is None for c in clean.cells if c.cell_type == "code"))
        code = [c for c in executed.cells if c.cell_type == "code"]
        self.assertEqual(len(code), 12)
        self.assertTrue(all(c.execution_count is not None for c in code))
        self.assertFalse(any(o.output_type == "error" for c in code for o in c.outputs))
        self.assertEqual(sum("image/png" in o.get("data", {}) for c in code for o in c.outputs), 7)

    def test_seven_graphs_are_nonblank_and_embedded_in_html(self):
        images = list((AREA / "resultados/graficos").glob("*.png"))
        self.assertEqual(len(images), 7)
        for path in images:
            with Image.open(path) as image:
                pixels = np.asarray(image.convert("RGB"))
                self.assertGreater(image.width, 1000)
                self.assertGreater(float(pixels.std()), 8., path.name)
                self.assertGreater(float((pixels.min(axis=2) < 230).mean()), .015, path.name)
        class EmbeddedImages(HTMLParser):
            def __init__(self):
                super().__init__()
                self.sources = []

            def handle_starttag(self, tag, attrs):
                if tag == "img":
                    self.sources.append(dict(attrs).get("src", ""))
        parser = EmbeddedImages()
        parser.feed((AREA / "resultados/classificacao_busca_ativa.html").read_text(encoding="utf-8"))
        self.assertEqual(sum(src.startswith("data:image/png;base64,") for src in parser.sources), 7)


if __name__ == "__main__":
    unittest.main()
