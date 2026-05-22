from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
WATCH_DIR = PROJECT_ROOT / "src"
ENTRYPOINT = WATCH_DIR / "automation.py"
POLL_INTERVAL_SECONDS = 0.5


def snapshot_python_files() -> dict[Path, int]:
    files = {}
    for path in WATCH_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        files[path] = path.stat().st_mtime_ns
    return files


def start_process() -> subprocess.Popen[bytes]:
    return subprocess.Popen([sys.executable, str(ENTRYPOINT)], cwd=PROJECT_ROOT)


def stop_process(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main() -> None:
    previous_snapshot = snapshot_python_files()
    process = start_process()

    try:
        while True:
            time.sleep(POLL_INTERVAL_SECONDS)
            current_snapshot = snapshot_python_files()

            if current_snapshot != previous_snapshot:
                print("Perubahan terdeteksi. Restart automation...")
                stop_process(process)
                previous_snapshot = current_snapshot
                process = start_process()
                continue

            if process.poll() is not None:
                process = start_process()
    except KeyboardInterrupt:
        print("\nDev runner dihentikan.")
    finally:
        stop_process(process)


if __name__ == "__main__":
    main()
