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

    def test_skip_if_screening_done_returns_true_when_completed(self):
        from unittest.mock import MagicMock
        mock_page = MagicMock()
        mock_row = MagicMock()
        mock_page.locator.return_value.filter.return_value = mock_row
        mock_row.get_by_text.return_value.count.return_value = 1

        screening = ScreeningNakes(mock_page, lambda value: value)
        result = screening._skip_if_screening_done("rowfrm000016", "Skrining Pertumbuhan Balita")

        self.assertTrue(result)
        mock_row.wait_for.assert_called_once()
        mock_row.get_by_text.assert_called_once_with("Selesai Pemeriksaan", exact=True)

    def test_skip_if_screening_done_returns_false_when_not_completed(self):
        from unittest.mock import MagicMock
        mock_page = MagicMock()
        mock_row = MagicMock()
        mock_page.locator.return_value.filter.return_value = mock_row
        mock_row.get_by_text.return_value.count.return_value = 0

        screening = ScreeningNakes(mock_page, lambda value: value)
        result = screening._skip_if_screening_done("rowfrm000016", "Skrining Pertumbuhan Balita")

        self.assertFalse(result)
        mock_row.wait_for.assert_called_once()
        mock_row.get_by_text.assert_called_once_with("Selesai Pemeriksaan", exact=True)


if __name__ == "__main__":
    unittest.main()

