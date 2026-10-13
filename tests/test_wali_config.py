import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HELPERS_DIR = Path(__file__).resolve().parents[1] / "src" / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from wali_config import (
    DEFAULT_PEKERJAAN_FALLBACK,
    DEFAULT_PERNIKAHAN_FALLBACK,
    WALI_ENV_KEYS,
    apply_wali_fallback,
    ensure_wali_credentials,
    get_wali_config,
    is_empty_value,
    is_wali_config_complete,
    save_wali_config_to_env,
)


class TestWaliConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_is_empty_value(self):
        self.assertTrue(is_empty_value(None))
        self.assertTrue(is_empty_value(""))
        self.assertTrue(is_empty_value("   "))
        self.assertTrue(is_empty_value("None"))
        self.assertTrue(is_empty_value("nan"))
        self.assertFalse(is_empty_value("3512144103800002"))
        self.assertFalse(is_empty_value(123))

    def test_is_wali_config_complete(self):
        incomplete = {
            "WALI_NIK": "3512144103800002",
            "WALI_NAMA": "ISNAWATI",
            "WALI_TGL_LAHIR": "1980-03-01",
            "WALI_GENDER": "",  # missing
        }
        self.assertFalse(is_wali_config_complete(incomplete))

        complete = {
            "WALI_NIK": "3512144103800002",
            "WALI_NAMA": "ISNAWATI",
            "WALI_TGL_LAHIR": "1980-03-01",
            "WALI_GENDER": "Perempuan",
        }
        self.assertTrue(is_wali_config_complete(complete))

    def test_save_wali_config_preserves_existing_env(self):
        env_file = self.temp_dir / ".env"
        initial_content = (
            "# Ini komentar\n"
            "CKG_USERNAME=test@gmail.com\n"
            "CKG_PASSWORD=secret\n"
            "EPUSKESMAS_URL=https://situbondo.epuskesmas.id\n"
        )
        env_file.write_text(initial_content, encoding="utf-8")

        config = {
            "WALI_NIK": "3512144103800002",
            "WALI_NAMA": "ISNAWATI",
            "WALI_TGL_LAHIR": "1980-03-01",
            "WALI_GENDER": "Perempuan",
        }
        save_wali_config_to_env(env_file, config)

        saved_text = env_file.read_text(encoding="utf-8")
        self.assertIn("CKG_USERNAME=test@gmail.com", saved_text)
        self.assertIn("CKG_PASSWORD=secret", saved_text)
        self.assertIn("EPUSKESMAS_URL=https://situbondo.epuskesmas.id", saved_text)
        self.assertIn("WALI_NIK=3512144103800002", saved_text)
        self.assertIn("WALI_NAMA=ISNAWATI", saved_text)
        self.assertIn("WALI_TGL_LAHIR=1980-03-01", saved_text)
        self.assertIn("WALI_GENDER=Perempuan", saved_text)

        # Test update existing keys
        updated_config = dict(config)
        updated_config["WALI_NAMA"] = "SITI FATIMAH"
        save_wali_config_to_env(env_file, updated_config)

        updated_text = env_file.read_text(encoding="utf-8")
        self.assertIn("WALI_NAMA=SITI FATIMAH", updated_text)
        self.assertNotIn("WALI_NAMA=ISNAWATI", updated_text)
        self.assertIn("CKG_USERNAME=test@gmail.com", updated_text)

    def test_ensure_wali_credentials_prompts_only_4_fields(self):
        env_file = self.temp_dir / ".env"
        env_file.write_text("CKG_USERNAME=test\n", encoding="utf-8")

        # Clear env vars
        for k in WALI_ENV_KEYS:
            os.environ.pop(k, None)

        user_inputs = [
            "3512144103800002",
            "ISNAWATI",
            "1980-03-01",
            "Perempuan",
        ]

        with patch("builtins.input", side_effect=user_inputs):
            cfg = ensure_wali_credentials(self.temp_dir)

        self.assertEqual(cfg["WALI_NIK"], "3512144103800002")
        self.assertEqual(cfg["WALI_NAMA"], "ISNAWATI")
        self.assertEqual(cfg["WALI_TGL_LAHIR"], "1980-03-01")
        self.assertEqual(cfg["WALI_GENDER"], "Perempuan")
        self.assertNotIn("WALI_PERNIKAHAN", cfg)
        self.assertNotIn("WALI_PEKERJAAN", cfg)

        # Verify saved in env_file
        saved = env_file.read_text(encoding="utf-8")
        self.assertIn("WALI_NIK=3512144103800002", saved)
        self.assertIn("WALI_GENDER=Perempuan", saved)

    def test_apply_wali_fallback_fills_empty_and_preserves_existing(self):
        wali_cfg = {
            "WALI_NIK": "3512144103800002",
            "WALI_NAMA": "ISNAWATI",
            "WALI_TGL_LAHIR": "1980-03-01",
            "WALI_GENDER": "Perempuan",
        }

        # Case 1: Row with empty wali fields, empty pernikahan, empty pekerjaan
        row_empty = {
            "nik": "3512062007200001",
            "nama_lengkap": "AHMAD",
            "no_whatsapp": "08123456789",
            "nik_wali": None,
            "nama_wali": "",
            "tgl_lahir_wali": "None",
            "gender_wali": "nan",
            "pernikahan": None,
            "pekerjaan": "",
            "no_whatsapp_wali": None,
        }

        filled = apply_wali_fallback(row_empty, wali_cfg)
        self.assertEqual(filled["nik_wali"], "3512144103800002")
        self.assertEqual(filled["nama_wali"], "ISNAWATI")
        self.assertEqual(filled["tgl_lahir_wali"], "1980-03-01")
        self.assertEqual(filled["gender_wali"], "Perempuan")
        self.assertEqual(filled["pernikahan"], DEFAULT_PERNIKAHAN_FALLBACK)
        self.assertEqual(filled["pekerjaan"], DEFAULT_PEKERJAAN_FALLBACK)
        self.assertEqual(filled["no_whatsapp_wali"], "08123456789")

        # Case 2: Row with existing values must NOT be overwritten
        row_existing = {
            "nik": "3512062007200001",
            "nama_lengkap": "AHMAD",
            "no_whatsapp": "08123456789",
            "nik_wali": "3512999999999999",
            "nama_wali": "BUDI SANTOSO",
            "tgl_lahir_wali": "1975-05-05",
            "gender_wali": "Laki-laki",
            "pernikahan": "Menikah",
            "pekerjaan": "Wiraswasta",
            "no_whatsapp_wali": "08999999999",
        }

        filled_existing = apply_wali_fallback(row_existing, wali_cfg)
        self.assertEqual(filled_existing["nik_wali"], "3512999999999999")
        self.assertEqual(filled_existing["nama_wali"], "BUDI SANTOSO")
        self.assertEqual(filled_existing["tgl_lahir_wali"], "1975-05-05")
        self.assertEqual(filled_existing["gender_wali"], "Laki-laki")
        self.assertEqual(filled_existing["pernikahan"], "Menikah")
        self.assertEqual(filled_existing["pekerjaan"], "Wiraswasta")
        self.assertEqual(filled_existing["no_whatsapp_wali"], "08999999999")


if __name__ == "__main__":
    unittest.main()
