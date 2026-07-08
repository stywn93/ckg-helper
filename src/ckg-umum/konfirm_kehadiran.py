import os
import re
import sys
from pathlib import Path

HELPERS_DIR = Path(__file__).resolve().parents[1] / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright_window_layout import launch_chromium_with_layout, pause_with_inspector_layout

from date_picker import DatePicker
from excel import ExcelStatusWorkbook, format_cell_value
from api_report import monitored_main

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
    page.goto("https://sehatindonesiaku.kemkes.go.id/ckg-pendaftaran-individu")
    page.wait_for_load_state("networkidle")

    checkbox = page.locator("input[name='verify']")
    if checkbox.count() > 0:
        checkbox = page.locator("input[name='verify']")
        checkbox.set_checked(True, force=True)
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


def searchPatient(page, data: dict, row_number: int, window_layout, date_picker: DatePicker) -> None:
    prepare_registration_page(page)
    print(f"{Colors.OKCYAN}Memulai proses pencarian...{Colors.ENDC}")

    date_picker.select(
        page.locator('[id="Tanggal Pemeriksaan"]'),
        format_cell_value(data["tgl_pemeriksaan"]),
    )

    page.locator("span:has-text('Nomor Tiket')").click()
    page.get_by_text("Nama", exact=True).click()
    page.locator('input#searchNik').fill(format_cell_value(data["nama_lengkap"]))
    page.keyboard.press("Enter")
    page.wait_for_load_state("networkidle")
    confirm_button = page.locator("button:has-text('Konfirmasi Hadir')").first
    try:
        confirm_button.wait_for(state="visible", timeout=3000)
    except PlaywrightTimeoutError:
        raise RuntimeError("Pencarian tidak memberikan hasil atau tombol Konfirmasi Hadir tidak muncul.")
    confirm_button.click()
    checkbox = page.locator("input[name='verify']")
    if checkbox.count() > 0:
        checkbox = page.locator("input[name='verify']")
        checkbox.set_checked(True, force=True)
        hadir_button = page.get_by_role("button", name="Hadir", exact=True)
        hadir_button.wait_for(state="visible", timeout=3000)
        hadir_button.click()
        page.wait_for_load_state("networkidle")
        page.get_by_role("button", name="Tutup", exact=True).click()

    #inspect again
    # pause_with_inspector_layout(page, window_layout)



def main() -> dict:
    excel_path = PROJECT_ROOT / "dataset" / "konfirm_kehadiran.xlsx"
    username = get_required_env(USERNAME_ENV)
    password = get_required_env(PASSWORD_ENV)
    excel = ExcelStatusWorkbook(excel_path)
    data_rows = excel.pending_rows()
    if not data_rows:
        print(f"{Colors.WARNING}Tidak ada data pada file Excel.{Colors.ENDC}")
        return {"status": "success"}

    any_failed = False

    with sync_playwright() as p:
        browser, window_layout = launch_chromium_with_layout(p)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        login_and_wait_for_profile(page, username, password)

        failed_rows = []
        date_picker = DatePicker()

        for row_entry in data_rows:
            index = row_entry["row_number"]
            data = row_entry["data"]
            try:
                searchPatient(page, data, index, window_layout, date_picker)
                excel.update_status(index, "SUCCESS")
            except Exception as exc:
                failed_rows.append(index)
                any_failed = True
                excel.update_status(index, f"FAILED: {exc}")
                # print(f"Baris Excel {index} gagal diproses: {exc}")

        context.close()
        browser.close()

    if any_failed:
        return {"status": "failed", "error_message": f"{len(failed_rows)} baris gagal diproses"}
    return {"status": "success"}

if __name__ == "__main__":
    monitored_main("konfirm_kehadiran", main)
