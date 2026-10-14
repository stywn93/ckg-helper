import io
import os
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Any

from ckg_helper import get_bundle_root
from src.helpers.api_report import report_execution
from src.helpers.power_management import SleepPreventer

ANSI_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Menghapus kode ANSI color/format terminal agar bersih di GUI."""
    return ANSI_REGEX.sub("", text)


class QueueWriter(io.TextIOBase):
    """
    Menangkap sys.stdout / sys.stderr dan memasukkannya ke dalam thread-safe queue.
    """

    def __init__(self, log_queue: queue.Queue, original_stream=None):
        super().__init__()
        self.log_queue = log_queue
        self.original_stream = original_stream

    def write(self, s: str) -> int:
        if s:
            clean = strip_ansi(s)
            self.log_queue.put(clean)
            if self.original_stream:
                try:
                    self.original_stream.write(s)
                    self.original_stream.flush()
                except Exception:
                    pass
        return len(s)

    def flush(self) -> None:
        if self.original_stream:
            try:
                self.original_stream.flush()
            except Exception:
                pass


class TaskExecutionWorker:
    """
    Worker yang mengeksekusi script otomatisasi Playwright di background subprocess.
    """

    def __init__(
        self,
        app_root: Path,
        option: dict[str, Any],
        log_queue: queue.Queue,
        on_started: Callable[[], None] | None = None,
        on_finished: Callable[[bool, str], None] | None = None,
    ):
        self.app_root = app_root
        self.option = option
        self.log_queue = log_queue
        self.on_started = on_started
        self.on_finished = on_finished
        self._thread: threading.Thread | None = None
        self._process: subprocess.Popen | None = None
        self._is_running = False
        self._is_stopped = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> None:
        if self._is_running:
            return
        self._is_running = True
        self._is_stopped = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """
        Menghentikan proses eksekusi seketika (terminate/kill).
        """
        self._is_stopped = True
        self._is_running = False
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=0.8)
                except subprocess.TimeoutExpired:
                    self._process.kill()
            except Exception:
                pass
        self.log_queue.put("\n⏹ Proses dihentikan oleh pengguna.\n")
        if self.on_finished:
            self.on_finished(False, "Proses dihentikan oleh pengguna.")

    def _run(self) -> None:
        if self.on_started:
            self.on_started()

        script_name_path = Path(self.option["script"])
        if getattr(sys, "frozen", False):
            script_path = get_bundle_root() / script_name_path
        else:
            script_path = self.app_root / script_name_path
        script_name = Path(self.option["script"]).stem

        self.log_queue.put("\n==========================================\n")
        self.log_queue.put(f"🚀 Memulai Tugas: {self.option.get('label')} - {self.option.get('detail')}\n")
        self.log_queue.put(f"📁 Target Script: {script_path.name}\n")
        self.log_queue.put("==========================================\n\n")

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["CKG_PROJECT_ROOT"] = str(self.app_root)

        start_time = time.monotonic()
        success = False
        message = ""

        try:
            with SleepPreventer():
                if getattr(sys, "frozen", False):
                    command = [sys.executable, "--run-script", str(script_name_path)]
                else:
                    command = [sys.executable, "-u", str(script_path)]

                self._process = subprocess.Popen(
                    command,
                    cwd=str(self.app_root),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

                # Baca output stdout line-by-line secara real-time
                if self._process.stdout:
                    for line in iter(self._process.stdout.readline, ""):
                        if not line and (self._process.poll() is not None or self._is_stopped):
                            break
                        clean = strip_ansi(line)
                        self.log_queue.put(clean)

                if self._process.stdout:
                    self._process.stdout.close()

                return_code = self._process.wait()

            if self._is_stopped:
                return

            if return_code == 0:
                success = True
                message = "Proses selesai dengan sukses."
                self.log_queue.put(f"\n✅ {message}\n")
            else:
                success = False
                message = f"Proses selesai dengan error (kode: {return_code})."
                self.log_queue.put(f"\n❌ {message}\n")

        except Exception as exc:
            if not self._is_stopped:
                duration_ms = int((time.monotonic() - start_time) * 1000)
                report_execution(script_name, "failed", duration_ms, str(exc))
                success = False
                message = f"Terjadi kesalahan: {exc}"
                self.log_queue.put(f"\n❌ {message}\n")
        finally:
            if not self._is_stopped:
                self._is_running = False
                if self.on_finished:
                    self.on_finished(success, message)
