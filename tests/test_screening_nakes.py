import unittest

from src.helpers.screening_nakes import ScreeningNakes


class TestScreeningNakes(unittest.TestCase):
    def setUp(self):
        self.screening = ScreeningNakes(None, lambda value: value)

    def test_normalizes_height_unit(self):
        self.assertEqual(
            self.screening.required({"tinggi_badan": "155 cm"}, "tinggi_badan"),
            "155",
        )

    def test_rejects_non_numeric_height(self):
        with self.assertRaisesRegex(ValueError, "harus berupa angka"):
            self.screening.required({"tinggi_badan": "seratus lima puluh lima"}, "tinggi_badan")


if __name__ == "__main__":
    unittest.main()
