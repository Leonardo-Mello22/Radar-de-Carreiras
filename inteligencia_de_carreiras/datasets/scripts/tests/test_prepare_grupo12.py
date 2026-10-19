import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare_grupo12 import OPTIONS, experience, integer, priorities, yes_no


class QuestionnaireParsingTests(unittest.TestCase):
    def test_yes_no_does_not_guess_invalid_answers(self):
        self.assertTrue(yes_no("Sim"))
        self.assertFalse(yes_no("Não"))
        self.assertIsNone(yes_no("dados desatualizados"))
        self.assertIsNone(yes_no(None))

    def test_exact_duration_conversion(self):
        for raw, months in [(0, 0), (18, 18), ("1 anos", 12), ("1 ano e 5 meses", 17),
                            ("Um ano e 6 meses ", 18), ("12 meses", 12), ("2 anos ", 24)]:
            with self.subTest(raw=raw):
                low, high, _ = experience(raw)
                self.assertEqual((low, high), (months, months))

    def test_reported_interval_is_not_imputed(self):
        self.assertEqual(experience("7 a 8 meses de estágio "), (7, 8, "intervalo_declarado"))
        self.assertEqual(experience("8 a 7 meses"), (None, None, "revisar_texto"))
        self.assertEqual(experience("muita experiência"), (None, None, "revisar_texto"))

    def test_internal_commas_do_not_split_options(self):
        value = ", ".join(OPTIONS[k] for k in ["salarios", "demanda_emprego", "habilidades"])
        choices, status = priorities(value)
        self.assertEqual(status, "valido")
        self.assertEqual(choices, ["salarios", "demanda_emprego", "habilidades"])

    def test_unrecognized_or_excess_options_are_flagged(self):
        self.assertEqual(priorities("outro"), ([], "revisar_opcoes"))
        self.assertEqual(priorities(", ".join(list(OPTIONS.values())[:4])), ([], "revisar_opcoes"))

    def test_salary_does_not_invent_units(self):
        self.assertEqual(integer("5"), 5)
        self.assertIsNone(integer("5 mil"))
        self.assertIsNone(integer("1.500"))
        self.assertIsNone(integer(None))


if __name__ == "__main__":
    unittest.main()
