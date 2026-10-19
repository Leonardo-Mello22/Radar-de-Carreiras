"""Integration checks run only when the authorized local research package exists."""
import hashlib
import json
import unittest
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[2]


class LocalResearchIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = DATA / "fontes_pesquisa_grupo12.json"
        responses = DATA / "tratados/pesquisa_grupo12_respostas.parquet"
        if not manifest.exists() or not responses.exists():
            raise unittest.SkipTest("Local research is private; provide authorized XLSX files to run integration tests.")
        cls.manifest = json.loads(manifest.read_text(encoding="utf-8"))
        cls.wide = pd.read_parquet(responses)

    def test_source_checksums(self):
        for source in self.manifest["arquivos"]:
            with (DATA / source["arquivo"]).open("rb") as stream:
                self.assertEqual(hashlib.file_digest(stream, "sha256").hexdigest(), source["sha256"])

    def test_long_tables_keep_distinct_grains(self):
        long = pd.read_parquet(DATA / "tratados/pesquisa_grupo12_respostas_longas.parquet")
        choices = pd.read_parquet(DATA / "tratados/pesquisa_grupo12_prioridades.parquet")
        self.assertEqual(len(long), len(self.wide) * 12)
        self.assertFalse(long.duplicated(["respondente_id", "pergunta_id"]).any())
        self.assertEqual(long.respondente_id.nunique(), len(self.wide))
        counts = choices.groupby("respondente_id").size().reindex(self.wide.respondente_id, fill_value=0)
        self.assertEqual(counts.to_list(), self.wide.prioridades_quantidade.to_list())
        self.assertTrue(counts.between(1, 3).all())

    def test_invalid_and_interval_answers_remain_flagged(self):
        report = self.manifest["questionario"]
        invalid = self.wide.usaria_ferramenta_original.notna() & self.wide.usaria_ferramenta.isna()
        self.assertEqual(int(invalid.sum()), report["q07_respostas_fora_dominio"])
        self.assertEqual(int(self.wide.expectativa_salarial_revisar.sum()), report["expectativas_sinalizadas"])
        ranged = self.wide.experiencia_ti_tratamento.eq("intervalo_declarado")
        self.assertTrue(self.wide.loc[ranged, "experiencia_ti_meses_exatos"].isna().all())
        self.assertNotIn("Timestamp", self.wide.columns)

    def test_phase01_questions_are_fully_specified(self):
        questions = pd.read_csv(DATA.parent / "01_plano_de_analise/matriz_perguntas_metricas.csv")
        self.assertEqual(set(questions.id), {f"P{i}" for i in range(1, 13)})
        self.assertFalse(questions.isna().any().any())
        datasets = {
            "CAGED": set(pd.read_parquet(DATA / "tratados/caged_ti.parquet").columns),
            "State of Data": set(pd.read_parquet(DATA / "tratados/state_of_data_carreiras.parquet").columns),
            "Pesquisa G12": set(self.wide.columns) | {"opcao_id"},
        }
        for question in questions.itertuples():
            columns = {c.split(" (")[0].strip() for c in question.colunas.split(";")}
            self.assertTrue(columns <= datasets[question.base], (question.id, columns - datasets[question.base]))
            self.assertNotEqual(question.objetivo_visual, question.metricas)

    def test_desk_research_is_not_verified_microdata(self):
        matrix = pd.read_parquet(DATA / "tratados/matriz_pesquisa_grupo12.parquet")
        self.assertEqual(len(matrix), self.manifest["matriz"]["registros"])
        self.assertEqual(int(matrix.url.notna().sum()), self.manifest["matriz"]["links_preservados"])
        self.assertFalse(matrix.evidencia_verificada_nesta_integracao.any())
        self.assertTrue(matrix.tipo_registro.eq("referencia_ou_hipotese").all())


if __name__ == "__main__":
    unittest.main()
