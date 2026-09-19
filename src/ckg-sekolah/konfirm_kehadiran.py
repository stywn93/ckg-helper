import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


HELPERS_DIR = Path(__file__).resolve().parents[1] / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

CKU_DIR = Path(__file__).resolve().parent.parent / "ckg-umum"
if str(CKU_DIR) not in sys.path:
    sys.path.insert(0, str(CKU_DIR))

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import click_delay  # noqa: F401
from playwright_window_layout import launch_chromium_with_layout


from excel import ExcelStatusWorkbook, ExcelAppendWorkbook, format_cell_value
from custom_exceptions import SkipRowException
from api_report import monitored_main
class Colors:
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

PROJECT_ROOT = Path(os.getenv("CKG_PROJECT_ROOT", Path(__file__).resolve().parents[2]))

load_dotenv(PROJECT_ROOT / ".env")

USERNAME_ENV = "CKG_USERNAME"
PASSWORD_ENV = "CKG_PASSWORD"
LOGIN_SUCCESS_TIMEOUT_MS = int(os.getenv("CKG_LOGIN_SUCCESS_TIMEOUT_MS", "60000"))

def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} belum diisi.")
    return value


def prepare_registration_page(page) -> None:
    page.goto("https://sehatindonesiaku.kemkes.go.id/ckg-pendaftaran-anak-sekolah")
    page.wait_for_load_state("networkidle")
    page.reload(wait_until="networkidle")

    checkbox = page.locator("input[name='verify']")
    if checkbox.count() > 0:
        checkbox = page.locator("input[name='verify']")
        checkbox.set_checked(True, force=True)
        # page.pause()
        page.locator("button:has-text('Setuju')").click()
        page.wait_for_load_state("networkidle")

def login_and_wait_for_profile(page, username: str, password: str) -> None:
    page.goto("https://sehatindonesiaku.kemkes.go.id/login")
    page.locator("input#email").fill(username)
    page.locator("input#password").fill(password)

    submit_button = page.locator("button[type='submit']").first
    if submit_button.count() > 0:
        submit_button.click()
    else:
        page.keyboard.press("Enter")

    try:
        page.wait_for_url(
            re.compile(r".*/profile(?:[/?#].*)?$"),
            timeout=LOGIN_SUCCESS_TIMEOUT_MS,
        )
        page.wait_for_load_state("networkidle")
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(
            "Login belum berhasil: halaman tidak redirect ke /profile "
            f"dalam {LOGIN_SUCCESS_TIMEOUT_MS} ms. URL saat ini: {page.url}"
        ) from exc


def register_single_entry(page, data: dict, row_number: int) -> None:
    prepare_registration_page(page)

    print("mencari field sekolah...")
    fSekolah = page.get_by_text("Pilih sekolah")
    if(fSekolah):
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field sekolah ditemukan{Colors.ENDC}")
        fSekolah.click()
    print("mencari input sekolah...")
    nama_sekolah_search = page.locator("#sekolah")
    if(nama_sekolah_search): 
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== input sekolah ditemukan{Colors.ENDC}")
        print(f"nama sekolah di excel : {format_cell_value(data['sekolah'])}")
        nama_sekolah_search.press_sequentially(format_cell_value(data["sekolah"]), delay=100)
        page.wait_for_selector("div.py-2.px-4.cursor-pointer", state="visible")
        print("mencari nama sekolah yang sesuai...")
        page.locator("div.py-2.px-4.cursor-pointer").first.click()

    print("mencari field kelas...")
    fKelas = page.get_by_text("Pilih kelas")
    if(fKelas):
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field kelas ditemukan{Colors.ENDC}")
        fKelas.click()
    print("mencari nama kelas...")
    print(f"nama kelas di excel : {format_cell_value(data["kelas"])}")
    nKelas = page.get_by_text(format_cell_value(data["kelas"]), exact=True)
    if(nKelas):
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== nama kelas ditemukan{Colors.ENDC}")
        nKelas.click()

    print("mencari field nomor tiket...")
    nTiket = page.get_by_text("Nomor Tiket")
    if(nTiket):
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== nomor tiket ditemukan{Colors.ENDC}")
        nTiket.click()
        print("mengganti field tiket dengan Nama...")
        nama = page.get_by_text("Nama", exact=True)
        if(nama):
            print(f"{Colors.OKGREEN}{Colors.BOLD}=== field nama ditemukan{Colors.ENDC}")
            nama.click()
            print("mencari field input nama...")
            nNama = page.locator("#searchNik")
            if(nNama):
                print(f"{Colors.OKGREEN}{Colors.BOLD}=== field input nama ditemukan{Colors.ENDC}")
                print(f"nama di excel : {format_cell_value(data["nama_lengkap"])}")
                nNama.press_sequentially(format_cell_value(data["nama_lengkap"]), delay=100)
                print("menjalankan aksi Enter")
                page.keyboard.press("Enter")
                print("menunggu hasil pencarian...")
                time.sleep(3)
                page.wait_for_load_state("networkidle")
                print("mencari tombol konfirmasi hadir...")
                buttonKonfirmasi = page.get_by_role("button", name="Konfirmasi Hadir")
    
    if buttonKonfirmasi.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol konfirmasi hadir ditemukan{Colors.ENDC}")
        buttonKonfirmasi.first.click()
        print("mencari checkbox verifikasi...")
        checkbox = page.locator("input[name='verify']")
        if checkbox.count() > 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}=== checkbox verifikasi ditemukan{Colors.ENDC}")
            checkbox = page.locator("input[name='verify']")
            print("mencoba mengklik checkbox...")
            checkbox.set_checked(True, force=True)
            print("mencari field nomor whatsapp...")
            wa = page.locator("input[name='Nomor Whatsapp']")
            if(wa):
                print(f"{Colors.OKGREEN}{Colors.BOLD}=== field nomor whatsapp ditemukan{Colors.ENDC}")
                print(f"nomor whatsapp di excel : {format_cell_value(data["whatsapp"])}")
                print("memasukkan nomor whatsapp...")
                wa.fill(format_cell_value(data["whatsapp"]))
            print("mencari tombol hadir...")
            hadir = page.get_by_role("button", name="Hadir", exact=True)
            if hadir.count() > 0:
                print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol hadir ditemukan{Colors.ENDC}")
                hadir.click()
            print("menunggu aksi selesai...")
            page.wait_for_load_state("networkidle")
            print("mencari tombol tutup...")
            tutup = page.get_by_role("button", name="Tutup", exact=True)
            if(tutup):
                print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol tutup ditemukan{Colors.ENDC}")
                tutup.click()
            print(f"{Colors.OKGREEN}{Colors.BOLD}============ Konfirmasi kehadiran berhasil ==========={Colors.ENDC}")

    else: 
        print(f"{Colors.WARNING}Pasien tidak ditemukan atau sudah mengkonfirmasi kehadiran {Colors.ENDC}")
        raise SkipRowException("Pasien tidak ditemukan atau sudah mengkonfirmasi kehadiran")
    

def main() -> dict:
    excel_path = PROJECT_ROOT / "dataset" / "konfirm_kehadiran_sekolah.xlsx"
    username = get_required_env(USERNAME_ENV)
    password = get_required_env(PASSWORD_ENV)
    excel = ExcelStatusWorkbook(excel_path)
    data_rows = excel.pending_rows()
    if not data_rows:
        print(f"{Colors.WARNING}Tidak ada data pada file Excel.{Colors.ENDC}")
        return {"status": "success"}

    any_failed = False

    with sync_playwright() as p:
        browser, _window_layout = launch_chromium_with_layout(p)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        login_and_wait_for_profile(page, username, password)

        failed_rows = []

        for row_entry in data_rows:
            index = row_entry["row_number"]
            data = row_entry["data"]
            try:
                register_single_entry(page, data, index)
                excel.update_status(index, "SUCCESS")
                konfirm_path = PROJECT_ROOT / "dataset" / "konfirm_kehadiran_sekolah.xlsx"
                konfirm_wb = ExcelAppendWorkbook(konfirm_path)
                konfirm_wb.append_row({
                    "nama_lengkap": format_cell_value(data["nama_lengkap"]),
                    "tgl_entri": datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d"),
                })
            except SkipRowException as exc:
                # excel.update_status(index, f"SKIPPED: {str(exc)}")
                excel.update_status(index, str(exc))
            except Exception as exc:
                failed_rows.append(index)
                any_failed = True
                excel.update_status(index, f"FAILED: {exc}")
        print(f"{Colors.OKCYAN}Pendaftaran selesai, silahkan buka kembali file Excel Anda. Jika ditemukan DUKCAPIL NOTICE maka jalankan kembali agar diproses ulang.{Colors.ENDC}")
        context.close()
        browser.close()

    if any_failed:
        return {"status": "failed", "error_message": f"{len(failed_rows)} baris gagal diproses"}
    return {"status": "success"}
if __name__ == "__main__":
    username = os.getenv("CKG_USERNAME", "unknown")
    monitored_main(f"pendaftaran - {username}", main)