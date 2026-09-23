import getpass
import os
import runpy
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
# Force PyInstaller to bundle openpyxl since subscripts are run dynamically via runpy
import openpyxl
from src.helpers.api_report import report_execution
from src.helpers.auto_update import __version__, check_for_update, install_update
from src.helpers.excel import DEFAULT_COMBINED_WORKBOOK_NAME, resolve_dataset

BANNER = r"""
  /$$$$$$  /$$   /$$  /$$$$$$        /$$   /$$                 /$$      /$$                                        
 /$$__  $$| $$  /$$/ /$$__  $$      | $$$ | $$                | $$  /$ | $$                                        
| $$  \__/| $$ /$$/ | $$  \__/      | $$$$| $$  /$$$$$$       | $$ /$$$| $$  /$$$$$$   /$$$$$$   /$$$$$$  /$$   /$$
| $$      | $$$$$/  | $$ /$$$$      | $$ $$ $$ /$$__  $$      | $$/$$ $$ $$ /$$__  $$ /$$__  $$ /$$__  $$| $$  | $$
| $$      | $$  $$  | $$|_  $$      | $$  $$$$| $$  \ $$      | $$$$_  $$$$| $$  \ $$| $$  \__/| $$  \__/| $$  | $$
| $$    $$| $$\  $$ | $$  \ $$      | $$\  $$$| $$  | $$      | $$$/ \  $$$| $$  | $$| $$      | $$      | $$  | $$
|  $$$$$$/| $$ \  $$|  $$$$$$/      | $$ \  $$|  $$$$$$/      | $$/   \  $$|  $$$$$$/| $$      | $$      |  $$$$$$$
 \______/ |__/  \__/ \______/       |__/  \__/ \______/       |__/     \__/ \______/ |__/      |__/       \____  $$
                                                                                                          /$$  | $$
                                                                                                         |  $$$$$$/
                                                                                                          \______/ 
"""


APP_NAME = f"CKG No Worry {__version__}"

_update_available: dict | None = None
USERNAME_ENV = "CKG_USERNAME"
PASSWORD_ENV = "CKG_PASSWORD"

MENU_OPTIONS = {
    "1": {
        "label": "CKG Umum - Pendaftaran Baru",
        "script": Path("src") / "ckg-umum" / "daftar_baru.py",
        "dataset_key": "pendaftaran_umum",
        "sheet": "pendaftaran_umum",
        "excel": Path("dataset") / "pendaftaran_umum.xlsx",
    },
    "3": {
        "label": "CKG Umum - Anak",
        "script": Path("src") / "ckg-umum" / "anak.py",
        "dataset_key": "anak",
        "sheet": "anak",
        "excel": Path("dataset") / "anak.xlsx",
    },
    "4": {
        "label": "CKG Umum - Remaja",
        "script": Path("src") / "ckg-umum" / "remaja.py",
        "dataset_key": "remaja",
        "sheet": "remaja",
        "excel": Path("dataset") / "remaja.xlsx",
    },
    "5": {
        "label": "CKG Umum - Dewasa",
        "script": Path("src") / "ckg-umum" / "dewasa.py",
        "dataset_key": "dewasa",
        "sheet": "dewasa",
        "excel": Path("dataset") / "dewasa.xlsx",
    },
    "6": {
        "label": "CKG Umum - Lansia",
        "script": Path("src") / "ckg-umum" / "lansia.py",
        "dataset_key": "lansia",
        "sheet": "lansia",
        "excel": Path("dataset") / "lansia.xlsx",
    },
    "7": {
        "label": "CKG Sekolah - Pendaftaran",
        "script": Path("src") / "ckg-sekolah" / "pendaftaran.py",
        "dataset_key": "pendaftaran_sekolah",
        "sheet": "pendaftaran_sekolah",
        "excel": Path("dataset") / "pendaftaran_sekolah.xlsx",
    },
    "8": {
        "label": "CKG Sekolah - Konfirmasi Kehadiran",
        "script": Path("src") / "ckg-sekolah" / "konfirm_kehadiran.py",
        "dataset_key": "konfirm_kehadiran_sekolah",
        "sheet": "konfirm_kehadiran_sekolah",
        "excel": Path("dataset") / "konfirm_kehadiran_sekolah.xlsx",
    },
    "9": {
        "label": "CKG Sekolah - Pelayanan",
        "script": Path("src") / "ckg-sekolah" / "pelayanan.py",
        "dataset_key": "pelayanan_sekolah",
        "sheet": "pelayanan_sekolah",
        "excel": Path("dataset") / "pelayanan_sekolah.xlsx",
    },
}

def show_banner():
    print(BANNER)

def get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", get_app_root())).resolve()


def pause(message: str = "Tekan Enter untuk kembali ke menu...") -> None:
    input(f"\n{message}")


def confirm_excel_closed() -> bool:
    options = ["ya", "tidak"]
    if not sys.stdin.isatty():
        return input("\nApakah file Excel sudah disimpan dan ditutup? (Ya/Tidak): ").strip().lower() in {
            "ya",
            "y",
        }

    selected_index = 0
    first_render = True
    print("\nApakah file Excel sudah disimpan dan ditutup?")
    print("Gunakan tombol ↑/↓ lalu Enter.\n")
    while True:
        if not first_render:
            print("\033[2A", end="")
        for index, option in enumerate(options):
            marker = ">" if index == selected_index else " "
            line = f"{marker} {option.capitalize()}"
            prefix = "\033[7m" if index == selected_index else ""
            print(f"\033[2K{prefix}{line}\033[0m")
        first_render = False

        key = read_menu_key()
        if key == "up":
            selected_index = next_menu_index(selected_index, -1, len(options))
        elif key == "down":
            selected_index = next_menu_index(selected_index, 1, len(options))
        elif key in {"\r", "\n"}:
            return selected_index == 0


def configure_playwright_browsers_path(app_root: Path) -> Path:
    browsers_path = app_root / "browsers"
    browsers_path.mkdir(exist_ok=True)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)
    return browsers_path


def load_app_env(app_root: Path) -> None:
    env_path = app_root / ".env"
    load_dotenv(env_path)
    os.environ["CKG_PROJECT_ROOT"] = str(app_root)
    configure_playwright_browsers_path(app_root)


def print_welcome(app_root: Path) -> None:
    # print(f"\n{APP_NAME}")
    # print("=" * len(APP_NAME))
    print("Panduan singkat:")
    print("- Pastikan file Excel sudah disimpan dan ditutup.")
    print("- Login CKG disimpan otomatis di file .env pada folder ini.")
    print("- Konsultasi via Telegram @stywn93")


def read_env_file(env_path: Path) -> dict[str, str]:
    values = {}
    if not env_path.exists():
        return values

    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def write_env_file(env_path: Path, values: dict[str, str]) -> None:
    lines = [
        f"{USERNAME_ENV}={values[USERNAME_ENV]}",
        f"{PASSWORD_ENV}={values[PASSWORD_ENV]}",
    ]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_credentials(app_root: Path) -> None:
    env_path = app_root / ".env"
    values = read_env_file(env_path)
    username = os.getenv(USERNAME_ENV) or values.get(USERNAME_ENV)
    password = os.getenv(PASSWORD_ENV) or values.get(PASSWORD_ENV)

    if username and password:
        os.environ[USERNAME_ENV] = username
        os.environ[PASSWORD_ENV] = password
        return

    print("\nKonfigurasi login belum lengkap.")
    print("Masukkan akun CKG. Data akan disimpan di file .env pada folder aplikasi.")

    while not username:
        username = input("Email/username CKG: ").strip()

    while not password:
        password = getpass.getpass("Password CKG: ").strip()

    values[USERNAME_ENV] = username
    values[PASSWORD_ENV] = password
    write_env_file(env_path, values)
    os.environ[USERNAME_ENV] = username
    os.environ[PASSWORD_ENV] = password
    print("Konfigurasi login tersimpan.")


def run_playwright_cli(args: list[str]) -> int:
    from playwright._impl._driver import compute_driver_executable, get_driver_env

    driver_executable, driver_cli = compute_driver_executable()
    completed = subprocess.run(
        [driver_executable, driver_cli, *args],
        env=get_driver_env(),
        check=False,
    )
    return completed.returncode


def chromium_is_installed() -> bool:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        executable_path = Path(playwright.chromium.executable_path)
    return executable_path.exists()


def ensure_chromium_installed() -> bool:
    try:
        if chromium_is_installed():
            return True
    except Exception:
        pass

    print("\nChromium browser belum terpasang.")
    print("Aplikasi perlu mengunduh browser otomatis satu kali saja.")
    print("Download dapat berlangsung beberapa menit, tergantung koneksi internet.")
    answer = input("Lanjutkan download sekarang? (Y/n): ").strip().lower()
    if answer not in {"y", "ya"}:
        print("Dibatalkan. Pilih menu ini lagi saat siap mengunduh Chromium.")
        return False

    print("\nMengunduh Chromium. Mohon tunggu sampai selesai...")
    exit_code = run_playwright_cli(["install", "chromium"])
    if exit_code != 0:
        print("\nDownload Chromium gagal.")
        print("Periksa koneksi internet, firewall/proxy kantor, atau antivirus, lalu coba lagi.")
        return False

    print("Chromium berhasil dipasang.")
    return True


def read_menu_key() -> str:
    if os.name == "nt":
        import msvcrt

        key = msvcrt.getwch()
        if key in {"\x00", "\xe0"}:
            return {"H": "up", "P": "down"}.get(msvcrt.getwch(), "")
        return key

    import termios
    import tty

    fd = sys.stdin.fileno()
    settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        key = sys.stdin.read(1)
        if key == "\x1b":
            sequence = sys.stdin.read(2)
            return {"[A": "up", "[B": "down", "OA": "up", "OB": "down"}.get(sequence, "")
        return key
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, settings)


def next_menu_index(index: int, direction: int, item_count: int) -> int:
    return (index + direction) % item_count


def print_menu(menu_keys: list[str], selected_index: int) -> None:
    print("\033[2J\033[H", end="")
    show_banner()
    print(f"{APP_NAME}")
    print("=" * len(APP_NAME))
    labels = {key: option["label"] for key, option in MENU_OPTIONS.items()}
    if _update_available:
        labels["u"] = f"⬇ Update v{_update_available['version_str']} tersedia!"
    labels["0"] = "Keluar"
    for index, key in enumerate(menu_keys):
        marker = ">" if index == selected_index else " "
        line = f"{marker} {key.upper()}. {labels[key]}"
        print(f"\033[7m{line}\033[0m" if index == selected_index else line)
    print("\nGunakan tombol ↑/↓ lalu Enter.")


def select_menu() -> str:
    menu_keys = list(MENU_OPTIONS)
    if _update_available:
        menu_keys.append("u")
    menu_keys.append("0")

    if not sys.stdin.isatty():
        return input("Pilih menu: ").strip().lower()

    selected_index = 0
    while True:
        print_menu(menu_keys, selected_index)
        key = read_menu_key()
        if key == "up":
            selected_index = next_menu_index(selected_index, -1, len(menu_keys))
        elif key == "down":
            selected_index = next_menu_index(selected_index, 1, len(menu_keys))
        elif key in {"\r", "\n"}:
            return menu_keys[selected_index]


def validate_excel_file(app_root: Path, option: dict[str, Path | str]) -> bool:
    dataset_key = str(option.get("dataset_key", ""))
    preferred_sheet = str(option.get("sheet", ""))
    target_path, sheet_name = resolve_dataset(dataset_key, preferred_sheet, project_root=app_root)

    if target_path.exists():
        return True

    print("\nFile data tidak ditemukan:")
    print(f"- File gabungan: {app_root / 'dataset' / DEFAULT_COMBINED_WORKBOOK_NAME} (sheet: '{preferred_sheet}')")
    print(f"- Atau file terpisah: {app_root / option['excel']}")
    print("Pastikan file Excel diletakkan di folder dataset.")
    return False


def run_selected_option(app_root: Path, option: dict[str, Path | str]) -> None:
    if not confirm_excel_closed():
        print("\nMenu dibatalkan. Tutup file Excel lalu pilih menu lagi.")
        pause()
        return

    if not validate_excel_file(app_root, option):
        pause()
        return

    ensure_credentials(app_root)
    if not ensure_chromium_installed():
        pause()
        return

    script_path = get_bundle_root() / option["script"]
    if not script_path.exists():
        print(f"\nScript tidak ditemukan: {script_path}")
        pause()
        return

    print(f"\nMenjalankan: {option['label']}")
    # print(f"File data: {app_root / option['excel']}")
    print("Jangan tutup browser atau terminal sampai proses selesai.\n")

    script_name = Path(option["script"]).stem

    old_cwd = Path.cwd()
    old_argv = sys.argv[:]
    sys.path.insert(0, str(script_path.parent))
    os.chdir(app_root)
    sys.argv = [str(script_path)]
    start = time.monotonic()
    try:
        runpy.run_path(str(script_path), run_name="__main__")
    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        report_execution(script_name, "failed", duration_ms, str(exc))
        raise
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)
        try:
            sys.path.remove(str(script_path.parent))
        except ValueError:
            pass

    print("\nProses selesai.")
    pause()


def main() -> None:
    global _update_available

    show_banner()
    app_root = get_app_root()
    load_app_env(app_root)
    print_welcome(app_root)

    print("\nMemeriksa update...", end=" ", flush=True)
    _update_available = check_for_update()
    if _update_available:
        print(f"v{_update_available['version_str']} tersedia!")
    else:
        print("Masih versi terbaru.")

    while True:
        choice = select_menu()
        if choice == "0":
            print("Keluar.")
            return

        if choice == "u":
            if _update_available:
                try:
                    install_update(app_root, _update_available)
                except Exception as exc:
                    print(f"\nUpdate gagal: {exc}")
                    pause()
            else:
                print("\nTidak ada update tersedia.")
                pause()
            continue

        option = MENU_OPTIONS.get(choice)
        if option is None:
            print("Pilihan tidak valid.")
            continue

        try:
            run_selected_option(app_root, option)
        except KeyboardInterrupt:
            print("\nProses dihentikan oleh user.")
            pause()
        except Exception as exc:
            print(f"\nTerjadi error: {exc}")
            pause()


if __name__ == "__main__":
    main()
