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

APP_NAME = "CKG Helper Beta 0.3.4"
USERNAME_ENV = "CKG_USERNAME"
PASSWORD_ENV = "CKG_PASSWORD"

MENU_OPTIONS = {
    "1": {
        "label": "Pendaftaran Baru",
        "script": Path("src") / "ckg-umum" / "daftar_baru.py",
        "excel": Path("dataset") / "pendaftaran_umum.xlsx",
    },
    "2": {
        "label": "Konfirmasi Kehadiran",
        "script": Path("src") / "ckg-umum" / "konfirm_kehadiran.py",
        "excel": Path("dataset") / "konfirm_kehadiran.xlsx",
    },
    "3": {
        "label": "CKG Umum Anak",
        "script": Path("src") / "ckg-umum" / "anak.py",
        "excel": Path("dataset") / "anak.xlsx",
    },
    "4": {
        "label": "CKG Umum Remaja",
        "script": Path("src") / "ckg-umum" / "remaja.py",
        "excel": Path("dataset") / "remaja.xlsx",
    },
    "5": {
        "label": "CKG Umum Dewasa",
        "script": Path("src") / "ckg-umum" / "dewasa.py",
        "excel": Path("dataset") / "dewasa.xlsx",
    },
    "6": {
        "label": "CKG Umum Lansia",
        "script": Path("src") / "ckg-umum" / "lansia.py",
        "excel": Path("dataset") / "lansia.xlsx",
    },
}


def get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", get_app_root())).resolve()


def pause(message: str = "Tekan Enter untuk kembali ke menu...") -> None:
    input(f"\n{message}")


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
    print(f"\n{APP_NAME}")
    print("=" * len(APP_NAME))
    print("Otomatisasi skrining CKG Sehat Indonesia Ku.")
    print()
    print("Panduan singkat:")
    print(f"- Folder data Excel: {app_root / 'dataset'}")
    print("- Jangan buka file Excel di aplikasi lain saat proses berjalan.")
    print("- Login CKG disimpan otomatis di file .env pada folder ini.")
    print("- Jika ada kendala, silahkan hubungi melalui Telegram @stywn93")


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
    print("CKG Helper perlu mengunduh browser otomatis satu kali saja.")
    print("Ukuran download dapat mencapai ratusan MB, tergantung versi Playwright.")
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


def print_menu() -> None:
    print(f"\n{APP_NAME}")
    print("=" * len(APP_NAME))
    for key, option in MENU_OPTIONS.items():
        print(f"{key}. {option['label']}")
    print("0. Keluar")


def validate_excel_file(app_root: Path, option: dict[str, Path | str]) -> bool:
    excel_path = app_root / option["excel"]
    if excel_path.exists():
        return True

    print(f"\nFile Excel tidak ditemukan: {excel_path}")
    print("Pastikan folder dataset berada satu folder dengan aplikasi.")
    return False


def run_selected_option(app_root: Path, option: dict[str, Path | str]) -> None:
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
    print(f"File data: {app_root / option['excel']}")
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


def run_data_generator(app_root: Path) -> None:
    from src.helpers.data_generator import generate_batch, append_to_excel, list_provinces, list_regencies

    print("\n=== Generator Data Penduduk ===")
    print("Menghasilkan data NIK, nama, tanggal lahir, dan gender.")
    print()

    try:
        count = int(input("Jumlah data yang ingin dibuat [10]: ").strip() or "10")
        if count < 1:
            print("Jumlah harus minimal 1.")
            return
    except ValueError:
        print("Input tidak valid.")
        return

    try:
        male_ratio = float(input("Persentase Laki-laki (0-100) [50]: ").strip() or "50")
        male_ratio = max(0.0, min(100.0, male_ratio))
    except ValueError:
        male_ratio = 50.0

    print("\nDaftar kode provinsi:")
    print(list_provinces())
    province = input("Kode provinsi (kosongkan untuk acak): ").strip()
    regency = ""
    if province:
        print()
        print(list_regencies(province))
        regency = input("Kode kota/kabupaten (kosongkan untuk acak): ").strip()

    try:
        min_age = int(input("Umur minimal [17]: ").strip() or "17")
        if min_age < 0:
            min_age = 17
    except ValueError:
        min_age = 17

    try:
        max_age = int(input("Umur maksimal [65]: ").strip() or "65")
        if max_age < 0:
            max_age = 65
    except ValueError:
        max_age = 65

    if min_age > max_age:
        min_age, max_age = max_age, min_age

    print(f"\nMembuat {count} data...")
    data = generate_batch(
        count=count,
        male_ratio=male_ratio,
        province_code=province if province else None,
        regency_code=regency if regency else None,
        min_age=min_age,
        max_age=max_age,
    )

    excel_path = app_root / "dataset" / "pendaftaran_umum.xlsx"
    rows_added = append_to_excel(excel_path, data)

    print(f"\nBerhasil menambahkan {rows_added} baris ke {excel_path}")
    print("\nContoh data:")
    for p in data[:3]:
        print(f"  {p['nik']} | {p['nama_lengkap']:25s} | {p['tgl_lahir']} | {p['gender']}")
    if len(data) > 3:
        print(f"  ... dan {len(data) - 3} lainnya")


def main() -> None:
    app_root = get_app_root()
    load_app_env(app_root)
    print_welcome(app_root)

    while True:
        print_menu()
        choice = input("Pilih menu: ").strip()
        if choice == "0":
            print("Keluar.")
            return

        if choice == "999":
            try:
                run_data_generator(app_root)
            except Exception as exc:
                print(f"\nTerjadi error: {exc}")
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
