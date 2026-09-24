import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "ckg-umum" / "daftar_baru.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("daftar_baru", MODULE_PATH)
DAFTAR_BARU = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DAFTAR_BARU)


class TestTargetSheetForAge(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(DAFTAR_BARU.target_sheet_for_age(0), "anak")
        self.assertEqual(DAFTAR_BARU.target_sheet_for_age(DAFTAR_BARU.CHILD_MAX_DAYS), "anak")
        self.assertEqual(DAFTAR_BARU.target_sheet_for_age(DAFTAR_BARU.CHILD_MAX_DAYS + 1), "remaja")
        self.assertEqual(DAFTAR_BARU.target_sheet_for_age(DAFTAR_BARU.TEENAGER_MAX_DAYS), "remaja")
        self.assertEqual(DAFTAR_BARU.target_sheet_for_age(DAFTAR_BARU.TEENAGER_MAX_DAYS + 1), "dewasa")
        self.assertEqual(DAFTAR_BARU.target_sheet_for_age(DAFTAR_BARU.ADULT_MAX_DAYS), "dewasa")
        self.assertEqual(DAFTAR_BARU.target_sheet_for_age(DAFTAR_BARU.ADULT_MAX_DAYS + 1), "lansia")


if __name__ == "__main__":
    unittest.main()
