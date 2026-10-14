import os
import queue
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from src.gui.runner import strip_ansi, QueueWriter, TaskExecutionWorker
from src.gui.app import CKGHelperApp
from src.epuskesmas.laporan_bpjs import (
    validate_date_range,
    EPUSKESMAS_URL_ENV,
    EPUSKESMAS_USERNAME_ENV,
    EPUSKESMAS_PASSWORD_ENV,
)


class TestGUIComponents(unittest.TestCase):
    def test_strip_ansi(self):
        raw = "\033[32mHello World\033[0m\n\033[2A"
        clean = strip_ansi(raw)
        self.assertEqual(clean, "Hello World\n")

    def test_queue_writer(self):
        q = queue.Queue()
        writer = QueueWriter(log_queue=q)
        writer.write("\033[31mError message\033[0m\n")
        self.assertFalse(q.empty())
        item = q.get()
        self.assertEqual(item, "Error message\n")

    def test_validate_date_range(self):
        today = datetime.today().date()
        today_str = today.strftime("%d-%m-%Y")
        yesterday_str = (today - timedelta(days=1)).strftime("%d-%m-%Y")
        four_days_ago_str = (today - timedelta(days=4)).strftime("%d-%m-%Y")
        tomorrow_str = (today + timedelta(days=1)).strftime("%d-%m-%Y")

        # 1. Valid range (hari ini)
        start, end = validate_date_range(today_str, today_str)
        self.assertEqual(start, today_str)
        self.assertEqual(end, today_str)

        # 2. Valid range (kemarin s/d hari ini)
        start, end = validate_date_range(yesterday_str, today_str)
        self.assertEqual(start, yesterday_str)
        self.assertEqual(end, today_str)

        # 3. Format invalid
        with self.assertRaises(ValueError):
            validate_date_range("2026-10-13", today_str)

        # 4. Tanggal awal > tanggal akhir
        with self.assertRaises(ValueError):
            validate_date_range(today_str, yesterday_str)

        # 5. Tanggal > hari ini
        with self.assertRaises(ValueError):
            validate_date_range(today_str, tomorrow_str)

        # 6. Rentang > 3 hari
        with self.assertRaises(ValueError):
            validate_date_range(four_days_ago_str, today_str)

    def test_worker_stop(self):
        # Uji kemampuan worker.stop() menghentikan subprocess
        q = queue.Queue()
        finished_results = []

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("import time\nwhile True:\n    time.sleep(0.1)\n")
            temp_script = Path(f.name)

        try:
            worker = TaskExecutionWorker(
                app_root=Path.cwd(),
                option={"script": temp_script, "label": "Test", "detail": "Test"},
                log_queue=q,
                on_finished=lambda success, msg: finished_results.append((success, msg)),
            )

            worker.start()
            time.sleep(0.3)
            self.assertTrue(worker.is_running)

            worker.stop()
            time.sleep(0.2)
            self.assertFalse(worker.is_running)
            self.assertEqual(len(finished_results), 1)
            self.assertIn("dihentikan", finished_results[0][1].lower())
        finally:
            temp_script.unlink(missing_ok=True)

    def test_gui_app_initialization_and_epuskesmas(self):
        app = CKGHelperApp(auto_check_update=False)
        try:
            # 1. Cek judul dan active category awal
            self.assertIn("CKG Helper", app.title())
            self.assertEqual(app.active_category, "CKG Umum")

            # Cek tombol Stop (default: disabled)
            self.assertTrue(hasattr(app, "btn_stop"))
            self.assertEqual(app.btn_stop.cget("state"), "disabled")

            # Konsol log aktif di CKG Umum
            self.assertNotEqual(app.console_container.grid_info(), {})

            # 2. Pindah ke ePuskesmas
            app._select_category("ePuskesmas")
            self.assertEqual(app.active_category, "ePuskesmas")
            self.assertEqual(app.header_title.cget("text"), "ePuskesmas")
            self.assertIsNotNone(app.current_selected_task)
            self.assertEqual(app.current_selected_task["detail"], "Ambil data dari ePuskesmas")

            # Cek preset tanggal
            app._set_date_yesterday()
            today_str = datetime.today().strftime("%d-%m-%Y")
            yesterday_str = (datetime.today() - timedelta(days=1)).strftime("%d-%m-%Y")
            self.assertEqual(app.picker_tgl_awal.get_date(), yesterday_str)
            self.assertEqual(app.picker_tgl_akhir.get_date(), today_str)
            self.assertEqual(app.ent_tgl_awal.get(), yesterday_str)
            self.assertEqual(app.ent_tgl_akhir.get(), today_str)

            app._set_date_today()
            self.assertEqual(app.picker_tgl_awal.get_date(), today_str)
            self.assertEqual(app.picker_tgl_akhir.get_date(), today_str)

            # Cek icon logo dari icon.png
            self.assertTrue(hasattr(app, "logo_image"))
            self.assertIsNotNone(app.logo_image)

            # 3. Pindah ke Pengaturan
            app._select_category("Pengaturan")
            self.assertEqual(app.active_category, "Pengaturan")
            self.assertTrue(hasattr(app, "ent_epus_url"))
            self.assertTrue(hasattr(app, "ent_epus_username"))
            self.assertTrue(hasattr(app, "ent_epus_password"))

            # Pastikan console_container tersembunyi (grid_info kosong) agar jendela lega
            self.assertEqual(app.console_container.grid_info(), {})

            # 4. Pindah ke Support & Donasi
            app._select_category("Support")
            self.assertEqual(app.active_category, "Support")
            self.assertEqual(app.header_title.cget("text"), "Support & Donasi")
            self.assertTrue(hasattr(app, "support_frame"))
            self.assertNotEqual(app.support_frame.grid_info(), {})
            self.assertEqual(app.console_container.grid_info(), {})
            self.assertEqual(app.task_view_frame.grid_info(), {})
            self.assertTrue(hasattr(app, "btn_support"))
            self.assertTrue(hasattr(app, "_open_saweria"))
            self.assertTrue(hasattr(app, "_open_telegram"))
            self.assertTrue(hasattr(app, "lbl_update_status"))
            self.assertTrue(hasattr(app, "btn_check_update"))
            self.assertTrue(hasattr(app, "btn_install_update"))
            self.assertTrue(hasattr(app, "btn_manual_download"))
            self.assertTrue(hasattr(app, "_check_update_async"))
            self.assertTrue(hasattr(app, "_open_manual_download"))
            self.assertTrue(hasattr(app, "_apply_auto_update"))

            # 5. Pindah kembali ke CKG Umum
            app._select_category("CKG Umum")
            self.assertEqual(app.active_category, "CKG Umum")
            self.assertNotEqual(app.console_container.grid_info(), {})
            self.assertEqual(app.support_frame.grid_info(), {})

            # 6. Uji _stop_task_execution langsung mengaktifkan tombol Mulai kembali
            mock_worker = MagicMock()
            mock_worker.is_running = True
            app.worker = mock_worker
            app.btn_run.configure(state="disabled")
            app.btn_stop.configure(state="normal")

            app._stop_task_execution()

            mock_worker.stop.assert_called_once()
            self.assertEqual(app.btn_run.cget("state"), "normal")
            self.assertEqual(app.btn_stop.cget("state"), "disabled")
            self.assertEqual(app.lbl_status.cget("text"), "Status: Dihentikan")

        finally:
            app.destroy()

    def test_gui_update_notification_states(self):
        from unittest.mock import patch
        app = CKGHelperApp(auto_check_update=False)
        try:
            # 1. Simulasi ada update baru
            sample_info = {
                "version": "v1.2.0",
                "version_str": "1.2.0",
                "download_url": "https://github.com/stywn93/CKG-Helper/releases/download/v1.2.0/test.zip",
                "checksum_url": None,
                "changelog": "- Fitur baru\n- Perbaikan bug",
            }
            with patch("src.gui.app.check_for_update", return_value=sample_info):
                t = app._check_update_async()
                if t:
                    t.join(timeout=2.0)
                app._poll_callbacks()
                app.update()

            self.assertIn("v1.2.0", app.lbl_update_status.cget("text"))
            self.assertIn("🟢", app.btn_support.cget("text"))
            self.assertNotEqual(app.frame_update_actions.grid_info(), {})
            self.assertNotEqual(app.frame_changelog.grid_info(), {})

            # 2. Simulasi sudah versi terbaru
            with patch("src.gui.app.check_for_update", return_value=None):
                t = app._check_update_async()
                if t:
                    t.join(timeout=2.0)
                app._poll_callbacks()
                app.update()

            self.assertIn("terbaru", app.lbl_update_status.cget("text").lower())
            self.assertNotIn("🟢", app.btn_support.cget("text"))
            self.assertEqual(app.frame_update_actions.grid_info(), {})
            self.assertEqual(app.frame_changelog.grid_info(), {})
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
