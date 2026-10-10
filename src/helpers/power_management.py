import ctypes
import os
import subprocess
import sys


ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


class SleepPreventer:
    """Mencegah layar dan sistem masuk ke mode sleep selama context manager aktif.

    Mendukung Windows via SetThreadExecutionState dan macOS via caffeinate.
    Aman dari exception agar kegagalan power management tidak mengganggu jalannya aplikasi.
    """

    def __init__(self) -> None:
        self._caffeinate_proc: subprocess.Popen | None = None
        self._active: bool = False

    @property
    def is_active(self) -> bool:
        return self._active

    def acquire(self) -> bool:
        if self._active:
            return True

        success = False
        try:
            if sys.platform == "win32":
                if hasattr(ctypes, "windll") and hasattr(ctypes.windll, "kernel32"):
                    res = ctypes.windll.kernel32.SetThreadExecutionState(
                        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
                    )
                    success = bool(res != 0)
            elif sys.platform == "darwin":
                # Cegah display sleep dan kaitkan dengan PID saat ini (-w PID)
                self._caffeinate_proc = subprocess.Popen(
                    ["caffeinate", "-d", "-w", str(os.getpid())],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                success = True
            else:
                # Platform lain (e.g. Linux) - fallback gracefully
                success = True
        except Exception:
            success = False

        self._active = success
        return success

    def release(self) -> bool:
        if not self._active:
            return True

        try:
            if sys.platform == "win32":
                if hasattr(ctypes, "windll") and hasattr(ctypes.windll, "kernel32"):
                    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            elif sys.platform == "darwin" and self._caffeinate_proc is not None:
                if self._caffeinate_proc.poll() is None:
                    self._caffeinate_proc.terminate()
                    try:
                        self._caffeinate_proc.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        self._caffeinate_proc.kill()
                self._caffeinate_proc = None
        except Exception:
            pass
        finally:
            self._active = False

        return True

    def __enter__(self) -> "SleepPreventer":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
