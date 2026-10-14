import getpass
import os
import re
import shutil
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime
import openpyxl
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

PROJECT_ROOT = Path(os.getenv("CKG_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
load_dotenv(PROJECT_ROOT / ".env")

EPUSKESMAS_URL_ENV = "EPUSKESMAS_URL"
EPUSKESMAS_USERNAME_ENV = "EPUSKESMAS_USERNAME"
EPUSKESMAS_PASSWORD_ENV = "EPUSKESMAS_PASSWORD"
LOGIN_TIMEOUT_MS = int(os.getenv("EPUSKESMAS_LOGIN_TIMEOUT_MS", "120000"))


COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[32m"
COLOR_RED = "\033[91m"
MAX_DATE_RANGE_DAYS = 3


def validate_date_range(tgl_awal: str, tgl_akhir: str) -> tuple[str, str]:
    today = datetime.today().date()
    today_str = today.strftime("%d-%m-%Y")
    try:
        dt_awal = datetime.strptime(tgl_awal, "%d-%m-%Y").date()
    except ValueError:
        raise ValueError(f"Format tanggal awal tidak valid ({tgl_awal})! Gunakan format dd-mm-yyyy.")

    try:
        dt_akhir = datetime.strptime(tgl_akhir, "%d-%m-%Y").date()
    except ValueError:
        raise ValueError(f"Format tanggal akhir tidak valid ({tgl_akhir})! Gunakan format dd-mm-yyyy.")

    if dt_awal > today:
        raise ValueError(f"Tanggal awal ({tgl_awal}) tidak boleh lebih besar daripada hari ini ({today_str})!")
    if dt_akhir > today:
        raise ValueError(f"Tanggal akhir ({tgl_akhir}) tidak boleh lebih besar daripada hari ini ({today_str})!")
    if dt_akhir < dt_awal:
        raise ValueError(f"Tanggal akhir ({tgl_akhir}) tidak boleh lebih kecil daripada tanggal awal ({tgl_awal})!")

    selisih_hari = (dt_akhir - dt_awal).days
    if selisih_hari > MAX_DATE_RANGE_DAYS:
        raise ValueError(f"Rentang tanggal melebihi batas maksimal ({selisih_hari} hari > {MAX_DATE_RANGE_DAYS} hari)!")

    return tgl_awal, tgl_akhir


def input_date_range() -> tuple[str, str]:
    # Jika di-set lewat GUI atau variabel environment
    env_start = os.getenv("EPUSKESMAS_START_DATE", "").strip()
    env_end = os.getenv("EPUSKESMAS_END_DATE", "").strip()
    if env_start and env_end:
        try:
            val_start, val_end = validate_date_range(env_start, env_end)
            print(f"Periode tanggal (dari GUI/env): {val_start} s/d {val_end}\n")
            return val_start, val_end
        except ValueError as err:
            print(f"{COLOR_RED}[Error Periode Tanggal] {err}{COLOR_RESET}")

    today = datetime.today().date()
    today_str = today.strftime("%d-%m-%Y")
    print("\n--- Filter Periode Tanggal Laporan (Format: dd-mm-yyyy) ---")

    while True:
        # 1. Input Tanggal Awal
        while True:
            tgl_awal = input(
                f"{COLOR_GREEN}Tanggal Awal  (dd-mm-yyyy) [tekan Enter untuk hari ini: {today_str}]: {COLOR_RESET}"
            ).strip()
            if not tgl_awal:
                tgl_awal = today_str
            try:
                dt_awal = datetime.strptime(tgl_awal, "%d-%m-%Y").date()
                if dt_awal > today:
                    print(f"{COLOR_RED}[Error] Tanggal awal ({tgl_awal}) tidak boleh lebih besar daripada hari ini ({today_str})!{COLOR_RESET}")
                    continue
                break
            except ValueError:
                print(f"{COLOR_RED}Format tanggal awal tidak valid! Gunakan format dd-mm-yyyy (misal: 01-10-2026).{COLOR_RESET}")

        # 2. Input Tanggal Akhir (fallback ke hari ini)
        while True:
            tgl_akhir = input(
                f"{COLOR_GREEN}Tanggal Akhir (dd-mm-yyyy) [tekan Enter untuk hari ini: {today_str}]: {COLOR_RESET}"
            ).strip()
            if not tgl_akhir:
                tgl_akhir = today_str
            try:
                dt_akhir = datetime.strptime(tgl_akhir, "%d-%m-%Y").date()
                if dt_akhir > today:
                    print(f"{COLOR_RED}[Error] Tanggal akhir ({tgl_akhir}) tidak boleh lebih besar daripada hari ini ({today_str})!{COLOR_RESET}")
                    continue
                break
            except ValueError:
                print(f"{COLOR_RED}Format tanggal akhir tidak valid! Gunakan format dd-mm-yyyy (misal: 11-10-2026).{COLOR_RESET}")

        # 3. Validasi tanggal akhir >= tanggal awal
        if dt_akhir < dt_awal:
            print(f"\n{COLOR_RED}[Error] Tanggal akhir ({tgl_akhir}) tidak boleh lebih kecil daripada tanggal awal ({tgl_awal})!{COLOR_RESET}")
            print(f"{COLOR_RED}Silakan masukkan kembali periode tanggal.{COLOR_RESET}\n")
            continue

        # 4. Validasi rentang maksimal 3 hari
        selisih_hari = (dt_akhir - dt_awal).days
        if selisih_hari > MAX_DATE_RANGE_DAYS:
            print(f"\n{COLOR_RED}[Error] Rentang tanggal melebihi batas maksimal ({selisih_hari} hari > {MAX_DATE_RANGE_DAYS} hari)!{COLOR_RESET}")
            print(f"{COLOR_RED}Maksimal rentang penarikan data adalah {MAX_DATE_RANGE_DAYS} hari agar proses tidak gagal/timeout.{COLOR_RESET}\n")
            continue

        print(f"Periode terpilih: {tgl_awal} s/d {tgl_akhir} ({selisih_hari + 1} hari)\n")
        return tgl_awal, tgl_akhir



def parse_birth_date(birth_place_and_date: str) -> str | None:
    if not birth_place_and_date:
        return None
    # Pola YYYY-MM-DD (misal: "SITUBONDO, 2001-10-22")
    match_iso = re.search(r"(\d{4}-\d{2}-\d{2})", str(birth_place_and_date))
    if match_iso:
        return match_iso.group(1)
    # Pola DD-MM-YYYY
    match_dmy = re.search(r"(\d{2}-\d{2}-\d{4})", str(birth_place_and_date))
    if match_dmy:
        d, m, y = match_dmy.group(1).split("-")
        return f"{y}-{m}-{d}"
    return None


DEFAULT_PHONE = "8123456789"


def clean_phone_number(raw_phone: str) -> str:
    if not raw_phone:
        return DEFAULT_PHONE
    phone = re.sub(r"[^\d]", "", str(raw_phone))
    if phone.startswith("62"):
        phone = phone[2:]
    elif phone.startswith("0"):
        phone = phone[1:]

    # Jika kosong atau hanya 1 digit (tidak valid), gunakan fallback default
    if not phone or len(phone) <= 1:
        return DEFAULT_PHONE
    return phone


def import_epuskesmas_to_ckg(downloaded_file: Path) -> tuple[int, int]:
    print(f"\n--- Memproses & Memindahkan Data Pasien ke ckg_data.xlsx ---")
    source_wb = openpyxl.load_workbook(downloaded_file, data_only=True)
    source_ws = source_wb.active

    # 1. Cari baris header yang memuat 'NIK' dan 'Nama Pasien'
    header_row_idx = None
    col_map = {}
    for idx, row in enumerate(source_ws.iter_rows(values_only=True), start=1):
        row_str = [str(c).strip() if c is not None else "" for c in row]
        if "NIK" in row_str and "Nama Pasien" in row_str:
            header_row_idx = idx
            for col_idx, col_name in enumerate(row_str):
                if col_name:
                    col_map[col_name] = col_idx
            break

    if not header_row_idx:
        raise ValueError("Header tabel (NIK & Nama Pasien) tidak ditemukan pada file unduhan!")

    # 2. Buka dataset/ckg_data.xlsx sheet pendaftaran_umum
    target_path = PROJECT_ROOT / "dataset" / "ckg_data.xlsx"
    if not target_path.exists():
        raise FileNotFoundError(f"File target {target_path} tidak ditemukan!")

    target_wb = openpyxl.load_workbook(target_path)
    if "pendaftaran_umum" not in target_wb.sheetnames:
        raise ValueError("Sheet 'pendaftaran_umum' tidak ditemukan di dataset/ckg_data.xlsx!")

    target_ws = target_wb["pendaftaran_umum"]

    # Kumpulkan NIK yang sudah ada untuk pencegahan duplikasi
    existing_niks = set()
    for row in target_ws.iter_rows(min_row=2, values_only=True):
        if row and row[0] is not None and str(row[0]).strip() not in {"", "None"}:
            existing_niks.add(str(row[0]).strip())

    # Cari baris pertama yang benar-benar kosong (cell NIK dan Nama kosong)
    write_row_idx = 2
    while True:
        cell_nik = target_ws.cell(row=write_row_idx, column=1).value
        cell_nama = target_ws.cell(row=write_row_idx, column=2).value
        nik_empty = cell_nik is None or str(cell_nik).strip() in {"", "None"}
        nama_empty = cell_nama is None or str(cell_nama).strip() in {"", "None"}
        if nik_empty and nama_empty:
            break
        write_row_idx += 1

    added_count = 0
    skipped_count = 0

    # 3. Baca dan petakan setiap baris pasien
    for row in source_ws.iter_rows(min_row=header_row_idx + 1, values_only=True):
        nik_raw = row[col_map.get("NIK", 4)] if col_map.get("NIK") is not None else None
        nama_raw = row[col_map.get("Nama Pasien", 2)] if col_map.get("Nama Pasien") is not None else None

        if not nik_raw or not str(nik_raw).strip() or str(nik_raw).strip() in {"None", "-"}:
            continue

        nik = str(nik_raw).strip()
        if nik in existing_niks:
            skipped_count += 1
            continue

        nama_lengkap = str(nama_raw).strip() if nama_raw else ""
        gender_raw = str(row[col_map.get("Jenis Kelamin", 8)]).strip().upper() if col_map.get("Jenis Kelamin") is not None and row[col_map.get("Jenis Kelamin")] else ""
        gender = "Perempuan" if gender_raw in {"P", "PEREMPUAN"} else "Laki-laki"

        tgl_lahir_raw = row[col_map.get("Tempat & Tgl.Lahir", 13)] if col_map.get("Tempat & Tgl.Lahir") is not None else None
        tgl_lahir = parse_birth_date(tgl_lahir_raw)

        phone_raw = row[col_map.get("No. Handpone", 7)] if col_map.get("No. Handpone") is not None else None
        no_whatsapp = clean_phone_number(phone_raw)

        domisili = str(row[col_map.get("Alamat", 9)]).strip() if col_map.get("Alamat") is not None and row[col_map.get("Alamat")] else None
        kec = str(row[col_map.get("Kecamatan", 11)]).strip().title() if col_map.get("Kecamatan") is not None and row[col_map.get("Kecamatan")] else None
        desa = str(row[col_map.get("Kelurahan", 12)]).strip().title() if col_map.get("Kelurahan") is not None and row[col_map.get("Kelurahan")] else None

        new_row = [
            nik,
            nama_lengkap,
            None,              # status kosong agar siap diproses CKG Helper
            tgl_lahir,
            gender,
            no_whatsapp,
            domisili,
            None,              # nik_wali
            None,              # nama_wali
            None,              # tgl_lahir_wali
            None,              # gender_wali
            None,              # no_whatsapp_wali
            None,              # pernikahan
            None,              # pekerjaan
            "Jawa Timur",      # prov
            "Kab. Situbondo",  # kab
            kec,
            desa,
        ]

        # Tulis langsung ke baris yang kosong
        for col_idx, val in enumerate(new_row, start=1):
            target_ws.cell(row=write_row_idx, column=col_idx, value=val)

        existing_niks.add(nik)
        added_count += 1
        write_row_idx += 1

    target_wb.save(target_path)
    return added_count, skipped_count


def get_epuskesmas_credentials() -> tuple[str, str, str]:
    url = os.getenv(EPUSKESMAS_URL_ENV, "").strip()
    username = os.getenv(EPUSKESMAS_USERNAME_ENV, "").strip()
    password = os.getenv(EPUSKESMAS_PASSWORD_ENV, "").strip()

    if not url:
        print("\n[Konfigurasi ePuskesmas]")
        url = input("Masukkan URL ePuskesmas (misal: https://situbondo.epuskesmas.id): ").strip()
    while not username:
        username = input("Username ePuskesmas: ").strip()
    while not password:
        password = getpass.getpass("Password ePuskesmas: ").strip()

    # Simpan kembali ke .env jika belum tersimpan
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith(f"{EPUSKESMAS_URL_ENV}="):
                new_lines.append(f"{EPUSKESMAS_URL_ENV}={url}")
                updated = True
            elif line.startswith(f"{EPUSKESMAS_USERNAME_ENV}="):
                new_lines.append(f"{EPUSKESMAS_USERNAME_ENV}={username}")
                updated = True
            elif line.startswith(f"{EPUSKESMAS_PASSWORD_ENV}="):
                new_lines.append(f"{EPUSKESMAS_PASSWORD_ENV}={password}")
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            new_lines.extend([
                "",
                "# Konfigurasi ePuskesmas",
                f"{EPUSKESMAS_URL_ENV}={url}",
                f"{EPUSKESMAS_USERNAME_ENV}={username}",
                f"{EPUSKESMAS_PASSWORD_ENV}={password}",
            ])
        env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    os.environ[EPUSKESMAS_URL_ENV] = url
    os.environ[EPUSKESMAS_USERNAME_ENV] = username
    os.environ[EPUSKESMAS_PASSWORD_ENV] = password

    return url, username, password


def run():
    url, username, password = get_epuskesmas_credentials()
    tgl_awal, tgl_akhir = input_date_range()

    # Pastikan URL langsung mengarah ke endpoint /login
    login_url = url.rstrip("/")
    if not login_url.endswith("/login"):
        login_url += "/login"

    with sync_playwright() as playwright:
        user_data_dir = PROJECT_ROOT / "browsers" / "epuskesmas_profile"
        user_data_dir.mkdir(parents=True, exist_ok=True)

        launch_kwargs = {
            "user_data_dir": str(user_data_dir),
            "headless": False,
            "accept_downloads": True,
            "ignore_default_args": ["--enable-automation"],
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        }

        try:
            # Gunakan Google Chrome lokal agar lolos verifikasi Cloudflare
            context = playwright.chromium.launch_persistent_context(channel="chrome", **launch_kwargs)
        except Exception:
            # Fallback ke Chromium default jika Chrome tidak ditemukan
            context = playwright.chromium.launch_persistent_context(**launch_kwargs)

        page = context.pages[0] if context.pages else context.new_page()

        # Sembunyikan tanda otomasi navigator.webdriver dari script bot detection
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            print(f"\n1. Mengakses {login_url}...")
            page.goto(login_url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            if "/home" in page.url:
                print("✓ Sesi login sebelumnya masih aktif! Langsung berada di halaman Home:", page.url)
            else:
                print("2. Sesi baru terdeteksi, mengisi username & password...")
                email_field = page.get_by_role("textbox", name="E-mail / No. HP / ID")
                email_field.wait_for(state="visible", timeout=15000)
                email_field.fill(username)

                password_field = page.get_by_role("textbox", name="kata kunci")
                password_field.wait_for(state="visible", timeout=15000)
                password_field.fill(password)

                print("3. Menunggu verifikasi Cloudflare & menekan tombol Login...")
                time.sleep(2)
                login_btn = page.get_by_role("button", name="Login")
                login_btn.wait_for(state="visible", timeout=15000)
                login_btn.click()

                print("Menunggu masuk ke halaman Home (maks 120 detik)...")
                try:
                    page.wait_for_url(lambda current_url: "/home" in current_url, timeout=LOGIN_TIMEOUT_MS)
                    page.wait_for_load_state("domcontentloaded")
                    print("\n✓ Login berhasil! Halaman saat ini:", page.url)
                except PlaywrightTimeoutError:
                    print("\n[Warning] Timeout menunggu halaman /home setelah login.")

            # 4. Klik Menu Laporan
            print("\n4. Mengklik menu Laporan...")
            menu_laporan = page.locator("#menu_laporan")
            menu_laporan.wait_for(state="visible", timeout=15000)
            menu_laporan.click()
            print("✓ Menu Laporan berhasil diklik.")
            menu_laporan_bpjs = page.locator("#menu_laporan_kunjungan_pasien_bpjs")
            menu_laporan_bpjs.wait_for(state="visible", timeout=15000)
            menu_laporan_bpjs.click()
            print("✓ Menu Laporan BPJS berhasil diklik.")

            # 5. Mengisi rentang tanggal & klik Tampilkan
            print(f"\n5. Mengisi periode laporan ({tgl_awal} s/d {tgl_akhir})...")
            input_dari = page.locator('input[name="search[dari_tanggal]"]')
            input_dari.wait_for(state="visible", timeout=15000)
            input_dari.fill(tgl_awal)

            input_sampai = page.locator('input[name="search[sampai_tanggal]"]')
            input_sampai.wait_for(state="visible", timeout=15000)
            input_sampai.fill(tgl_akhir)

            print("6. Mengklik tombol Tampilkan...")
            btn_tampilkan = page.get_by_role("button", name="Tampilkan", exact=True)
            btn_tampilkan.wait_for(state="visible", timeout=15000)
            btn_tampilkan.click()
            page.wait_for_load_state("domcontentloaded")
            print("✓ Tombol Tampilkan berhasil diklik. Menunggu data siap...")
            time.sleep(3)

            # 7. Download File Export Excel
            print("\n7. Mengunduh laporan via tombol Export Excel...")
            btn_export = page.get_by_role("button", name="Export Excel", exact=True)
            btn_export.wait_for(state="visible", timeout=30000)

            with page.expect_download(timeout=60000) as download_info:
                btn_export.click()
            download = download_info.value

            suggested_name = download.suggested_filename or "Laporan_Kunjungan_BPJS.xlsx"
            download_dest = PROJECT_ROOT / "dataset" / suggested_name

            print(f"Menunggu proses unduhan '{suggested_name}' selesai...")
            download.save_as(download_dest)
            print(f"✓ File laporan berhasil diunduh dan disimpan ke:\n  {download_dest}")

            # 8. Proses & Masukkan Data ke ckg_data.xlsx
            added, skipped = import_epuskesmas_to_ckg(download_dest)
            print(f"\n{COLOR_GREEN}✓ Proses Import Berhasil!{COLOR_RESET}")
            print(f"  • {added} data pasien baru berhasil ditambahkan ke sheet 'pendaftaran_umum'.")
            if skipped > 0:
                print(f"  • {skipped} data pasien dilewati karena NIK sudah ada sebelumnya.")
        except PlaywrightTimeoutError as err:
            print(f"\n{COLOR_RED}[Gagal] Waktu tunggu habis (Timeout):{COLOR_RESET}")
            if "Export Excel" in str(err):
                print(f"{COLOR_RED}Tombol 'Export Excel' belum muncul. Kemungkinan server ePuskesmas masih memuat data atau tidak ada kunjungan pasien pada periode tersebut.{COLOR_RESET}")
            else:
                print(f"{COLOR_RED}Halaman web ePuskesmas tidak merespons dalam batas waktu yang ditentukan.{COLOR_RESET}")
            print(f"{COLOR_RED}Browser tetap dibiarkan terbuka agar Anda dapat memeriksa kondisi halaman.{COLOR_RESET}")
        except Exception as err:
            print(f"\n{COLOR_RED}[Gagal] Terjadi kesalahan: {err}{COLOR_RESET}")
            print(f"{COLOR_RED}Browser tetap dibiarkan terbuka agar Anda dapat memeriksa kondisi halaman.{COLOR_RESET}")
        finally:
            try:
                import termios
                termios.tcflush(sys.stdin, termios.TCIFLUSH)
            except Exception:
                pass

            input(f"\n{COLOR_GREEN}Tekan Enter di terminal ini untuk menutup browser dan kembali ke menu utama...{COLOR_RESET}")
            try:
                context.close()
            except Exception:
                pass


if __name__ == "__main__":
    run()
