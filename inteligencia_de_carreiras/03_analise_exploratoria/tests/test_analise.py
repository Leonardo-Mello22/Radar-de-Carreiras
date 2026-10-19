import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

AREA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AREA))
from analise import active_target, correlation_pair, salary_summary, technology_rates


class AnalysisRulesTests(unittest.TestCase):
    def test_salary_quantiles_suppressed_below_threshold(self):
        frame = pd.DataFrame({"grupo": ["baixo"] * 29 + ["suficiente"] * 30, "salario_real": np.arange(59) + 1000})
        result = salary_summary(frame, ["grupo"]).set_index("grupo")
        self.assertTrue(pd.isna(result.loc["baixo", "p50"]))
        self.assertTrue(np.isfinite(result.loc["suficiente", "p50"]))

    def test_technology_missing_is_not_negative(self):
        values = pd.array([True] * 4 + [False] * 30 + [None] * 6, dtype="boolean")
        frame = pd.DataFrame({c: values for c in ["usa_sql", "usa_python", "usa_r", "usa_power_bi", "usa_aws", "usa_gcp", "usa_azure"]})
        result = technology_rates(frame)
        self.assertTrue(result.n_respondidos.eq(34).all())
        self.assertTrue(result.ausentes.eq(6).all())
        self.assertTrue(np.allclose(result.proporcao, 4 / 34))

    def test_active_target_preserves_missing_and_rejects_unknown(self):
        from analise import ACTIVE
        values = active_target(pd.Series([next(iter(ACTIVE)), None]))
        self.assertTrue(values.iloc[0])
        self.assertTrue(pd.isna(values.iloc[1]))
        with self.assertRaises(ValueError):
            active_target(pd.Series(["talvez"]))

    def test_constant_or_small_correlation_is_not_invented(self):
        n, rho = correlation_pair(pd.DataFrame({"x": [1] * 40, "y": range(40)}), "x", "y")
        self.assertEqual(n, 40)
        self.assertTrue(np.isnan(rho))


class ExecutedAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (AREA / "registro_execucao.json").exists():
            raise unittest.SkipTest("Execute the analysis before checking delivered outputs.")
        cls.public = AREA / "resultados_fontes_publicas/tabelas"

    def test_movement_counts_reconcile_without_nested_double_count(self):
        totals = pd.read_csv(self.public / "P2_totais.csv").set_index("regiao")
        self.assertEqual(int(totals.loc["Brasil", ["admissoes", "desligamentos"]].sum()), 118564)
        self.assertEqual(int(totals.loc["Pernambuco", ["admissoes", "desligamentos"]].sum()), 2305)

    def test_salary_pairs_are_matched_and_sufficient(self):
        frame = pd.read_csv(self.public / "P3_pares_comparaveis.csv")
        self.assertFalse(frame.duplicated(["uf_sigla", "cbo_codigo", "competencia"]).any())
        self.assertTrue(frame.n_admissao.ge(30).all() and frame.n_desligamento.ge(30).all())

    def test_search_target_reconciles_source_counts(self):
        frame = pd.read_csv(self.public / "P8_classes.csv")
        self.assertEqual(int(frame.n.sum()), 4734)
        self.assertEqual(int(frame.loc[frame.classe.eq("Busca ativa"), "n"].iloc[0]), 1630)

    def test_public_tables_do_not_include_private_research(self):
        self.assertFalse(any(path.name.startswith(("P9_", "P10_", "P11_", "P12_")) for path in self.public.glob("*.csv")))

    def test_notebook_executed_and_versioned_source_is_clean(self):
        import nbformat
        source = nbformat.read(AREA / "analise_exploratoria.ipynb", as_version=4)
        full = nbformat.read(AREA / "resultados_locais/analise_exploratoria_executada.ipynb", as_version=4)
        self.assertTrue(all(not c.outputs and c.execution_count is None for c in source.cells if c.cell_type == "code"))
        self.assertTrue(all(c.execution_count is not None for c in full.cells if c.cell_type == "code"))
        self.assertFalse(any(out.output_type == "error" for c in full.cells if c.cell_type == "code" for out in c.outputs))
        self.assertTrue(any("image/png" in out.get("data", {}) for c in full.cells if c.cell_type == "code" for out in c.outputs))

    def test_execution_record_matches_current_code(self):
        import hashlib
        report = json.loads((AREA / "registro_execucao.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "EXECUTADO_SEM_ERROS")
        for name, digest in report["codigo_sha256"].items():
            self.assertEqual(hashlib.sha256((AREA / name).read_bytes()).hexdigest(), digest)

    def test_graphs_have_nonblank_pixels(self):
        from PIL import Image
        paths = list((AREA / "resultados_fontes_publicas/graficos").glob("*.png"))
        paths += list((AREA / "resultados_locais/pesquisa_grupo12/graficos").glob("*.png"))
        self.assertGreaterEqual(len(paths), 16)
        for path in paths:
            pixels = np.asarray(Image.open(path).convert("RGB"))
            self.assertGreater(pixels.shape[1], 900, path.name)
            self.assertGreater((pixels < 230).any(axis=2).mean(), .01, path.name)
            height, width = pixels.shape[:2]
            central = pixels[int(.20 * height):int(.75 * height), int(.30 * width):int(.85 * width)]
            self.assertGreater(central.std(), 2, path.name)


if __name__ == "__main__":
    unittest.main()
