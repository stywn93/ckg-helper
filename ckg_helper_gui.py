"""
CKG Helper - Graphical User Interface (GUI)
Menggunakan CustomTkinter untuk antarmuka desktop modern.
"""
import os
import runpy
import sys
from pathlib import Path

# Pastikan root direktori ada di sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def configure_worker_output() -> None:
    """Keep worker output flowing to the parent GUI process immediately."""
    for stream_name, fd in (("stdout", 1), ("stderr", 2)):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            try:
                stream = os.fdopen(os.dup(fd), "w", buffering=1)
                setattr(sys, stream_name, stream)
            except OSError:
                continue

        try:
            stream.reconfigure(line_buffering=True, write_through=True)
        except (AttributeError, OSError):
            pass


def run_script(script_name: str) -> int:
    """Run a bundled automation script in a worker subprocess."""
    configure_worker_output()
    bundle_root = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)).resolve()
    script_path = Path(script_name)
    if not script_path.is_absolute():
        script_path = bundle_root / script_path

    if not script_path.exists():
        print(f"Script tidak ditemukan: {script_path}")
        return 1

    project_root = Path(os.getenv("CKG_PROJECT_ROOT", PROJECT_ROOT)).resolve()
    old_cwd = Path.cwd()
    old_argv = sys.argv[:]
    sys.path.insert(0, str(bundle_root))
    sys.path.insert(0, str(script_path.parent))
    os.chdir(project_root)
    sys.argv = [str(script_path)]
    try:
        runpy.run_path(str(script_path), run_name="__main__")
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)
        for path in (str(script_path.parent), str(bundle_root)):
            try:
                sys.path.remove(path)
            except ValueError:
                pass
    return 0


def main():
    from src.gui.app import main as run_gui

    run_gui()

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--run-script":
        raise SystemExit(run_script(sys.argv[2]))
    main()
