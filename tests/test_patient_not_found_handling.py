import importlib.util
import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from src.helpers.custom_exceptions import PatientNotFoundException
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# Load remaja module dynamically due to hyphen in folder name "ckg-umum"
REMAJA_PATH = Path(__file__).resolve().parents[1] / "src" / "ckg-umum" / "remaja.py"
spec = importlib.util.spec_from_file_location("remaja_module", REMAJA_PATH)
remaja_module = importlib.util.module_from_spec(spec)
sys.modules["remaja_module"] = remaja_module
spec.loader.exec_module(remaja_module)


class TestPatientNotFoundHandling(unittest.TestCase):
    def test_patient_not_found_exception_is_exception(self):
        """PatientNotFoundException must be a subclass of Exception."""
        self.assertTrue(issubclass(PatientNotFoundException, Exception))
        exc = PatientNotFoundException("Pasien tidak ditemukan pada semua status pemeriksaan.")
        self.assertEqual(str(exc), "Pasien tidak ditemukan pada semua status pemeriksaan.")

    def test_search_patient_raises_patient_not_found_exception(self):
        """When search_patient_with_status times out on all statuses, PatientNotFoundException should be raised."""
        with patch.object(remaja_module, "search_patient_with_status") as mock_search_with_status:
            mock_search_with_status.side_effect = PlaywrightTimeoutError("Timeout exceeded")
            mock_page = MagicMock()

            with self.assertRaises(remaja_module.PatientNotFoundException) as ctx:
                remaja_module.search_patient(mock_page, {"nama": "Test Pasien", "cari_by_nik": False}, 1)

            self.assertIn("Pasien tidak ditemukan pada semua status pemeriksaan.", str(ctx.exception))
            # It should have checked all 3 statuses (Belum, Sedang, Selesai)
            self.assertEqual(mock_search_with_status.call_count, 3)


if __name__ == "__main__":
    unittest.main()
