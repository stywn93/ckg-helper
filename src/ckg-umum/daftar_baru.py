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

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright_window_layout import launch_chromium_with_layout

from date_picker import DatePicker
from excel import ExcelStatusWorkbook, ExcelAppendWorkbook, format_cell_value
from custom_exceptions import SkipRowException
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

def wait_for_first_visible(page, locators_dict, timeout=5000):
    """
    Waits for the first element in the dict to become visible.
    Returns the key of the element that became visible.
    """
    start_time = time.time()
    while time.time() - start_time < (timeout / 1000):
        for key, locator in locators_dict.items():
            if locator.is_visible():
                return key
        time.sleep(0.5)
    raise PlaywrightTimeoutError("None of the expected buttons appeared")

def handle_periksa_kembali(page, data: dict, date_picker: DatePicker) -> None:
    btn_recheck = page.locator("button:has-text('Periksa Kembali')").first
    btn_success = page.locator("button:has-text('Lanjutkan')").first
    try:
        btn_recheck.wait_for(state="visible", timeout=3000)
        btn_recheck.click()
        btn_recheck.wait_for(state="hidden", timeout=3000)
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

def isi_data_wali(page, data: dict, date_picker: DatePicker) -> None:
    page.locator("input#nik\\ wali").fill(format_cell_value(data["nik_wali"]))
    page.locator('input[name="Nama Lengkap Wali"]').fill(format_cell_value(data["nama_wali"]))

    date_picker.select(page.locator('[id="Tanggal Lahir"] .mx-input-wrapper').filter(has_text="Pilih Tanggal Lahir"),format_cell_value(data["tgl_lahir_wali"]),)

    page.locator("div:has(> .text-gray-4:text('Pilih Jenis Kelamin'))").click()
    page.locator(".max-h-\\[250px\\]").get_by_text(format_cell_value(data["gender_wali"]), exact=True).click()
    page.locator("label").filter(has_text="No. Whatsapp Wali").locator('input[name="Nomor whatsapp"]').fill(
        format_cell_value(data["no_whatsapp_wali"])
    )

def register_single_entry(page, data: dict, row_number: int, date_picker: DatePicker) -> None:
    prepare_registration_page(page)
    print()
    print(f"{Colors.BOLD}======================={Colors.ENDC}")
    print(f"{Colors.OKBLUE}Nama : {format_cell_value(data['nama_lengkap'])}{Colors.ENDC}")
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

    # Select a specific day button by exact day number (avoids "1" matching "11", "12"...)
    dob = datetime.strptime(format_cell_value(data['tgl_lahir']), "%Y-%m-%d")
    today = datetime.now(ZoneInfo("Asia/Jakarta"))

    # Raw day difference
    # if diff > 21915 or diff < 2191 then do isi data wali
    diff = today.date() - dob.date()
    # print(f"Total days: {diff.days}")

    day = datetime.now().day
    # day = 7
    day_button = page.locator("button").filter(
        has=page.locator("span.font-bold", has_text=re.compile(rf"^{day}$"))
    )
    day_button.click()
    if diff.days > 21915 or diff.days < 2191:
        # print("try to call isi data wali")
        isi_data_wali(page, data, date_picker)
    page.get_by_role("button", name="Selanjutnya").click()
    # page.pause()



    # Opsi 1 jika sudah menerima CKG
    # Opsi 2 jika belum menerima CKG
    locators = {
        "quota_habis" : page.get_by_role("button", name="Lanjut", exact=True),
        "cari_individu": page.get_by_role("button", name="Cari Individu", exact=True), #jika sudah menerima CKG
        "lanjutkan": page.get_by_role("button", name="Lanjutkan", exact=True), #jika NIK valid dan belum menerima CKG
        "periksa_kembali": page.get_by_role("button", name="Periksa Kembali", exact=True), #jika NIK tidak valid
    }

    found = wait_for_first_visible(page, locators)
    print(found)
    # page.pause()
    if found == "quota_habis":
        print("Quota Pemeriksaan habis")
        locators["quota_habis"].click()
        # page.pause()
        next_found = wait_for_first_visible(page, locators)
        print(f"next_found : {next_found}")
        if next_found == "periksa_kembali":
            locators["periksa_kembali"].click()
            page.locator("input#tidak-punya-nik[type='checkbox']").click(force=True)
            page.get_by_role("button", name="Selanjutnya", exact=True).click()
            next_found_2 = wait_for_first_visible(page, locators)
            if(next_found_2 == "quota_habis"):
                locators["quota_habis"].click()
                next_found_3 = wait_for_first_visible(page, locators)
                if(next_found_3 == "lanjutkan"):
                    locators["lanjutkan"].click()
            elif next_found_2 == "lanjutkan":
                locators["lanjutkan"].click()
        elif next_found == "cari_individu":
            print(f"{Colors.WARNING}pasien ini sudah menerima CKG{Colors.ENDC}")
            raise SkipRowException("Pasien ini sudah menerima CKG")
        elif next_found == "lanjutkan":
            locators["lanjutkan"].click()
        # print(f"next_found {next_found}")
    elif found == "periksa_kembali":
        locators["periksa_kembali"].click()
        page.locator("input#tidak-punya-nik[type='checkbox']").click(force=True)
        isi_data_wali(page, data, date_picker)
        page.get_by_role("button", name="Selanjutnya", exact=True).click()
        next_found = wait_for_first_visible(page, locators)
        if next_found == "lanjutkan":
            locators["lanjutkan"].click()
    elif found == "cari_individu":
        print(f"{Colors.WARNING}pasien ini sudah menerima CKG{Colors.ENDC}")
        raise SkipRowException("Pasien ini sudah menerima CKG")
    else:
        print(f"{Colors.WARNING}pasien belum menerima CKG{Colors.ENDC}")
        page.get_by_role("button", name="Lanjutkan", exact=True).click()


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
    print(f"{Colors.OKCYAN}Mohon tunggu sedang menunggu respon dari server CKG secara lengkap...{Colors.ENDC}")
    # page.pause()
    page.wait_for_timeout(1500)
    # Seharusnya menunggu apakah tombol pilih muncul
    # jika tombol pilih muncul maka klik tombol pilih
    # jika tombol pilih di-klik maka klik Daftarkan dengan NIK
    # jika Daftarkan dengan NIK diklik, maka tunggu respon
    # jika ada tombol Ok, maka Raise Exception
    # jika tidak muncul maka klik Daftarkan tanpa NIK

    locators = {
        "dengan_nik": page.get_by_role("button", name="Pilih"),
        "tanpa_nik": page.get_by_role("button", name="Daftarkan tanpa NIK")
    }
    nik_found = wait_for_first_visible(page, locators)
    print(f"nik_found = {nik_found}")
    if(nik_found == "dengan_nik"):
        locators["dengan_nik"].click()
        print(f"{Colors.OKCYAN}NIK ditemukan, silahkan tunggu...{Colors.ENDC}")
        page.get_by_role("button", name="Daftarkan dengan NIK").click()


    elif(nik_found == "tanpa_nik"):
        locators["tanpa_nik"].click()

    page.wait_for_load_state("networkidle")

    locators = {
        "exception": page.get_by_role("button", name="Ok", exact=True),
        "tutup": page.get_by_role("button", name="Tutup")
    }
    exception_found = wait_for_first_visible(page, locators)
    if (exception_found == "exception"):
        locators["exception"].click()
        raise SkipRowException("Ada error dari Server CKG - Biasanya terkait NIK yang tidak valid")
    else:
        locators["tutup"].click()
        print(f"{Colors.OKGREEN}{Colors.BOLD}============ Pendaftaran Berhasil ==========={Colors.ENDC}")


def main() -> dict:
    excel_path = PROJECT_ROOT / "dataset" / "pendaftaran_umum.xlsx"
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
        date_picker = DatePicker()

        for row_entry in data_rows:
            index = row_entry["row_number"]
            data = row_entry["data"]
            try:
                register_single_entry(page, data, index, date_picker)
                excel.update_status(index, "SUCCESS")
                konfirm_path = PROJECT_ROOT / "dataset" / "konfirm_kehadiran.xlsx"
                konfirm_wb = ExcelAppendWorkbook(konfirm_path)
                konfirm_wb.append_row({
                    "nama_lengkap": format_cell_value(data["nama_lengkap"]),
                    "tgl_pemeriksaan": datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d"),
                })
            except SkipRowException as exc:
                # excel.update_status(index, f"SKIPPED: {str(exc)}")
                excel.update_status(index, str(exc))
            except Exception as exc:
                failed_rows.append(index)
                any_failed = True
                excel.update_status(index, f"FAILED: {exc}")
                # print(f"Baris Excel {index} gagal diproses: {exc}")
        print(f"{Colors.OKCYAN}Pendaftaran selesai, silahkan buka kembali file Excel Anda. Jika ditemukan DUKCAPIL NOTICE maka jalankan kembali agar diproses ulang.{Colors.ENDC}")
        context.close()
        browser.close()

    if any_failed:
        return {"status": "failed", "error_message": f"{len(failed_rows)} baris gagal diproses"}
    return {"status": "success"}

if __name__ == "__main__":
    username = os.getenv("CKG_USERNAME", "unknown")
    monitored_main(f"daftar_baru - {username}", main)