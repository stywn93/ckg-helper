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
from playwright_window_layout import launch_chromium_with_layout

from date_picker import DatePicker
from excel import ExcelStatusWorkbook, format_cell_value

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
    # page.reload(wait_until="networkidle")

    checkbox = page.locator("input[name='verify']")
    if checkbox.count() > 0:
        checkbox = page.locator("input[name='verify']")
        checkbox.set_checked(True, force=True)
        page.locator("button:has-text('Setuju')").click()
        page.wait_for_load_state("networkidle")

    page.get_by_role("button", name="Daftar Baru").click()


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


def register_single_entry(page, data: dict, row_number: int, date_picker: DatePicker) -> None:
    prepare_registration_page(page)

    nik_input = page.locator("form input#nik")
    nik_input.fill(format_cell_value(data["nik"]))
    page.locator('input#Nama\\ Lengkap').fill(format_cell_value(data["nama_lengkap"]))

    date_picker.select(
        page.locator("#Tanggal\\ Lahir .mx-input-wrapper"),
        format_cell_value(data["tgl_lahir"]),
    )
    page.get_by_text("Pilih jenis kelamin", exact=True).click()
    page.locator("div.absolute.top-13.z-2000").get_by_text(
        format_cell_value(data["gender"]),
        exact=True,
    ).click()
    
    page.locator('input#No\\ Whatsapp').fill(format_cell_value(data["no_whatsapp"]))


    panel = page.locator("div:has(> .text-\\[20px\\].font-bold:text('Tanggal Pemeriksaan'))")
    tanggal = panel.get_by_role("button", name=format_cell_value(data["tgl_pemeriksaan"])).nth(1)
    try:
        tanggal.wait_for(state="visible", timeout=3000)
        tanggal.click()
        page.get_by_role("button", name="Selanjutnya").click()
    except PlaywrightTimeoutError:
        page.pause()
        page.get_by_role("button", name="Selanjutnya").click()

    btn_recheck = page.locator("button:has-text('Periksa Kembali')").first
    btn_success = page.locator("button:has-text('Lanjutkan')").first
    try:
        btn_recheck.wait_for(state="visible", timeout=3000)
        btn_recheck.click()
        btn_recheck.wait_for(state="hidden", timeout=5000)
        checkbox = page.locator("input[name='noNik']")
        checkbox.set_checked(True, force=True)
        page.locator("input#nik\\ wali").fill(format_cell_value(data["nik_wali"]))
        page.locator('input[name="Nama Lengkap Wali"]').fill(format_cell_value(data["nama_wali"]))

        date_picker.select(
            page.locator('[id="Tanggal Lahir"] .mx-input-wrapper').filter(has_text="Pilih Tanggal Lahir"),
            format_cell_value(data["tgl_lahir_wali"]),
        )

        page.locator("div:has(> .text-gray-4:text('Pilih Jenis Kelamin'))").click()
        page.locator(".max-h-\\[250px\\]").get_by_text(format_cell_value(data["gender_wali"]), exact=True).click()
        page.locator("label").filter(has_text="No. Whatsapp Wali").locator('input[name="Nomor whatsapp"]').fill(
            format_cell_value(data["no_whatsapp_wali"])
        )
        page.get_by_role("button", name="Selanjutnya").click()
        page.locator("button:has-text('Lanjutkan')").click()

    except PlaywrightTimeoutError:
        btn_success.click()

    page.get_by_text("Pilih status pernikahan", exact=True).click()
    page.get_by_text(format_cell_value(data["pernikahan"]), exact=True).click()

    page.get_by_text("Pilih pekerjaan", exact=True).click()
    page.get_by_text(format_cell_value(data["pekerjaan"]), exact=True).click()

    page.get_by_text("Pilih alamat domisili", exact=True).click()
    page.get_by_text(format_cell_value(data["prov"]), exact=True).click()
    page.get_by_text(format_cell_value(data["kab"]), exact=True).click()
    page.get_by_text(format_cell_value(data["kec"]), exact=True).click()
    page.get_by_text(format_cell_value(data["desa"]), exact=True).click()
    page.locator("textarea#detail-domisili").fill(format_cell_value(data["domisili"]))

    page.get_by_role("button", name="Selanjutnya").click()
    page.wait_for_timeout(1500)
    page.get_by_role("button", name="Daftarkan Tanpa NIK").click()
    page.wait_for_timeout(1500)
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name="Tutup").click()
    # page.goto("https://sehatindonesiaku.kemkes.go.id/ckg-pelayanan")
    # page.wait_for_load_state("networkidle")

def main():
    excel_path = PROJECT_ROOT / "dataset" / "pendaftaran_umum.xlsx"
    username = get_required_env(USERNAME_ENV)
    password = get_required_env(PASSWORD_ENV)
    excel = ExcelStatusWorkbook(excel_path)
    data_rows = excel.pending_rows()
    if not data_rows:
        print("Tidak ada data pada file Excel.")
        return

    with sync_playwright() as p:
        browser, _window_layout = launch_chromium_with_layout(p)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        login_and_wait_for_profile(page, username, password)

        failed_rows = []
        date_picker = DatePicker()

        for row_entry in data_rows:
            index = row_entry["row_number"]
            data = row_entry["data"]
            try:
                register_single_entry(page, data, index, date_picker)
                excel.update_status(index, "SUCCESS")
            except Exception as exc:
                failed_rows.append(index)
                excel.update_status(index, f"FAILED: {exc}")
                # print(f"Baris Excel {index} gagal diproses: {exc}")

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
