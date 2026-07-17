import os
import inspect
import traceback
import re
import sys
from pathlib import Path

HELPERS_DIR = Path(__file__).resolve().parents[1] / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))
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

from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from playwright_window_layout import launch_chromium_with_layout

# coba gunakan helper
from excel import ExcelStatusWorkbook, format_cell_value
from screening_mandiri import ScreeningMandiri
from api_report import monitored_main
from screening_nakes import ScreeningNakes
load_dotenv(PROJECT_ROOT / ".env")

USERNAME_ENV = "CKG_USERNAME"
PASSWORD_ENV = "CKG_PASSWORD"
DEBUG_RAISE_ERRORS_ENV = "CKG_DEBUG_RAISE_ERRORS"
SCREENING_UI_TIMEOUT_MS = int(os.getenv("CKG_SCREENING_UI_TIMEOUT_MS", "5000"))
PATIENT_SEARCH_TIMEOUT_MS = int(os.getenv("CKG_PATIENT_SEARCH_TIMEOUT_MS", "3000"))
EXAMINATION_STATUS_OPTIONS = {
    "1": "Belum Pemeriksaan",
    "2": "Sedang Pemeriksaan",
    "3": "Selesai Pemeriksaan",
}
EXAMINATION_STATUS_SEARCH_ORDER = list(EXAMINATION_STATUS_OPTIONS.values())
MONTH_LABELS = {
    "01": "Jan",
    "02": "Feb",
    "03": "Mar",
    "04": "Apr",
    "05": "Mei",
    "06": "Jun",
    "07": "Jul",
    "08": "Agt",
    "09": "Sep",
    "10": "Okt",
    "11": "Nov",
    "12": "Des",
}
MONTH_TO_NUMBER = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "Mei": 5,
    "Jun": 6,
    "Jul": 7,
    "Agt": 8,
    "Sep": 9,
    "Okt": 10,
    "Nov": 11,
    "Des": 12,
}
LOGIN_SUCCESS_TIMEOUT_MS = int(os.getenv("CKG_LOGIN_SUCCESS_TIMEOUT_MS", "60000"))
DEWASA_MANDIRI_LAKI_SCREENINGS = [
    "do_demografi_dewasa",
    "do_risiko_kanker_usus",
    "do_risiko_tb",
    "do_hati",
    "do_keswa",
    "do_risiko_kanker_paru",
    "do_perilaku_merokok",
    "do_aktivitas_fisik",
]
DEWASA_MANDIRI_PEREMPUAN_SCREENINGS = [
    "do_demografi_dewasa_perempuan",
    "do_risiko_kanker_usus",
    "do_risiko_tb",
    "do_hati",
    "do_leher_rahim",
    "do_keswa",
    "do_risiko_kanker_paru",
    "do_perilaku_merokok",
    "do_aktivitas_fisik",
]
DEWASA_NAKES_LAKI_SCREENINGS = [
    "do_gizi_laki",
    "do_gula_darah_dewasa",
    "do_tekanan_darah_dewasa",
    "do_risiko_tb",
    "do_tb",
    "do_frambusia",
    "do_kusta",
    "do_skabies",
    "do_telinga_mata",
    "do_karies",
    "do_periodontal",
    "do_ppok",
    "do_kadar_co",
    "do_lipid",
    "do_fibrosis",
    "do_hepatitis",
    "do_fungsi_ginjal",
    "do_kerusakan_ginjal",
    "do_jantung",
    "do_kanker_usus",
    "do_kanker_paru",
    "do_hiv",
    "do_sifilis",
]
DEWASA_NAKES_PEREMPUAN_SCREENINGS = [
    "do_gizi_perempuan",
    "do_gula_darah_dewasa",
    "do_tekanan_darah_dewasa",
    "do_risiko_tb",
    "do_tb",
    "do_frambusia",
    "do_kusta",
    "do_skabies",
    "do_telinga_mata",
    "do_telinga_mata_18_39",
    "do_karies",
    "do_periodontal",
    "do_ppok",
    "do_kadar_co",
    "do_lipid",
    "do_fibrosis",
    "do_hepatitis",
    "do_fungsi_ginjal_perempuan",
    "do_kerusakan_ginjal",
    "do_kanker_payudara",
    "do_hpv_dna",
    "do_inspekulo_iva",
    "do_jantung",
    "do_kanker_usus",
    "do_kanker_paru",
    "do_catin_perempuan",
    "do_hiv",
    "do_sifilis",
]

def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} belum diisi.")
    return value


def prepare_page(page) -> None:
    page.goto("https://sehatindonesiaku.kemkes.go.id/ckg-pelayanan")
    page.wait_for_load_state("networkidle")

    checkbox = page.locator("input[name='verify']")
    if checkbox.count() > 0:
        checkbox = page.locator("input[name='verify']")
        checkbox.set_checked(True, force=True)
        page.locator("button:has-text('Setuju')").click()
        page.wait_for_load_state("networkidle")

    sameLocation = page.locator("input[name='sameLocation']")
    if sameLocation.count() > 0:
        sameLocation = page.locator("input[name='sameLocation']")
        sameLocation.set_checked(True, force=True)
        page.locator("button:has-text('Simpan')").click()
        page.wait_for_load_state("networkidle")
    # print("end of prepare_page")


def login_and_wait_for_profile(page, username: str, password: str) -> None:
    page.goto("https://sehatindonesiaku.kemkes.go.id/ckg-pelayanan")
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


def search_patient_with_status(page, data: dict, examination_status: str) -> None:
    prepare_page(page)
    page.locator("div.cursor-pointer.px-3").filter(has_text=examination_status).click()
    page.locator("div.mx-input-wrapper").click()
    
    search_by_nik = format_cell_value(data["cari_by_nik"])

    if search_by_nik:
        page.locator("div").filter(has_text=re.compile(r"^Nama$")).nth(3).click()
        page.get_by_text("NIK").click()
        nik_field = page.get_by_role("textbox", name="0/").click()
        page.keyboard.type(format_cell_value(data["nik"]))
    else:
        batas_awal = format_cell_value(data["batas_awal"])
        batas_akhir = format_cell_value(data["batas_akhir"])
        page.locator(f'td.cell[title="{batas_awal}"]').first.click()
        page.locator(f'td.cell[title="{batas_akhir}"]').first.click()
        page.locator("span:has-text('Nama')").click()
        page.get_by_text("Nama", exact=True).nth(0).click()
        page.locator("input#searchNik").fill(format_cell_value(data["nama"]))
    
    page.keyboard.press("Enter")
    page.wait_for_timeout(1000)
    page.wait_for_load_state("networkidle")
    page.locator("button:has-text('Mulai')").first.click(timeout=PATIENT_SEARCH_TIMEOUT_MS)


def search_patient(page, data: dict, row_number: int) -> str:
    last_error = None

    for examination_status in EXAMINATION_STATUS_SEARCH_ORDER:
        try:
            print(
                f"{Colors.OKCYAN}Baris {row_number}: mencari pasien pada status "
                f"{examination_status}.{Colors.ENDC}"
            )
            search_patient_with_status(page, data, examination_status)
            print(
                f"{Colors.OKGREEN}Baris {row_number}: pasien ditemukan pada status "
                f"{examination_status}.{Colors.ENDC}"
            )
            break
        except PlaywrightTimeoutError as exc:
            last_error = exc
            print(
                f"{Colors.WARNING}Baris {row_number}: pasien tidak ditemukan pada status "
                f"{examination_status}.{Colors.ENDC}"
            )
    else:
        raise RuntimeError(
            "Pasien tidak ditemukan pada semua status pemeriksaan."
        ) from last_error

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)
    for remaining_seconds in range(3, 0, -1):
        print(f"{Colors.OKCYAN}Menunggu halaman pemeriksaan tampil... {remaining_seconds} detik{Colors.ENDC}")
        page.wait_for_timeout(1000)
    # print("end of search_patient")
    return examination_status

# ---------- Pelayanan Oleh Nakes ------------

def do_pemeriksaan_check(page, selector: str, checked: bool) -> None:
    checkbox = page.locator(selector)
    if checked is False and checkbox.is_checked():
        # print("status pemeriksaan is False")
        checkbox.click(force=True)
        page.get_by_role("button", name="Tidak Periksa").click()
    elif checked is True:
        # print("status pemeriksaan is True")
        # print("selector ", selector)
        # page.pause()
        if checkbox.is_checked() != checked:
            checkbox.click()
        # checkbox.click()
        # page.locator(selector).set_checked(checked, force=True)


def close_active_screening_form(page) -> None:
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)


def get_screening_form_id(method) -> str | None:
    try:
        source = inspect.getsource(method)
    except OSError:
        return None

    match = re.search(r"rowfrm\d+", source)
    if match is None:
        return None
    return match.group(0)


def is_screening_form_available(page, method) -> bool:
    form_id = get_screening_form_id(method)
    if form_id is None:
        return True

    try:
        page.locator(f'[id="{form_id}"]').wait_for(
            state="visible",
            timeout=SCREENING_UI_TIMEOUT_MS,
        )
        return True
    except PlaywrightTimeoutError:
        return False


def run_screening_steps(screening, method_names: list[str], data: dict, row_number: int, page) -> None:
    for method_name in method_names:
        method = getattr(screening, method_name, None)
        if method is None:
            print(f"{Colors.WARNING}Skip {method_name}: function tidak ditemukan.{Colors.ENDC}")
            continue

        if not is_screening_form_available(page, method):
            print(
                f"{Colors.WARNING}Skip {method_name}: elemen UI form tidak ditemukan "
                f"dalam {SCREENING_UI_TIMEOUT_MS} ms.{Colors.ENDC}"
            )
            continue

        try:
            print(f"{Colors.OKCYAN}Menjalankan {method_name}{Colors.ENDC}")
            method(data, row_number)
            page.wait_for_load_state("networkidle")
        except PlaywrightTimeoutError as exc:
            print(f"{Colors.WARNING}Skip {method_name}: elemen UI tidak ditemukan atau tidak tampil. Detail: {exc}{Colors.ENDC}")
            close_active_screening_form(page)


def main() -> dict:
    excel_path = PROJECT_ROOT / "dataset" / "dewasa.xlsx"
    username = get_required_env(USERNAME_ENV)
    password = get_required_env(PASSWORD_ENV)
    excel = ExcelStatusWorkbook(excel_path)
    data_rows = excel.pending_rows()
    if not data_rows:
        skipped_rows = excel.summary["skipped_rows"]
        if skipped_rows:
            print(
                f"{Colors.WARNING}Tidak ada data yang perlu diproses. "
                f"Baris {skipped_rows} dilewati karena status sudah selesai.{Colors.ENDC}"
            )
            print(f"{Colors.OKCYAN}Kosongkan kolom status untuk memproses ulang baris tersebut.{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}Tidak ada data pada file Excel.{Colors.ENDC}")
            print("")
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
                examination_status = search_patient(page, data, index)
                # search_patient(page, data, index)
                badge = page.locator("div.border-rd-full.px-3.py-1").first
                badge.wait_for(state="visible", timeout=15000)
                badge_text = badge.inner_text().strip()
                print(badge_text)
                if badge_text != "Dewasa":
                    excel.update_status(index, f"Gagal - ini bukan pasien dewasa. Ini adalah pasien {badge_text}")
                    any_failed = True
                    page.wait_for_load_state("networkidle")
                    continue

                if badge_text == "Dewasa":
                    gender_locator = (
                        page.locator("div.flex.flex-col.gap-2")
                        .filter(has_text="Jenis Kelamin")
                        .locator("div.font-bold")
                    )
                    gender = gender_locator.inner_text().strip()
                    if gender == "Laki-Laki":
                        print(f"{Colors.OKCYAN}Skrining Laki-Laki Dewasa{Colors.ENDC}")
                        print(f"{Colors.BOLD}============== Skrining Mandiri Dimulai =============={Colors.ENDC}")
                        if examination_status == "Belum Pemeriksaan":
                            #butuh perbaikan di sini untuk memilih tanggal
                            page.locator("button.btn-fill-primary:has-text('Mulai Pemeriksaan')").click()
                            page.locator("button.btn-fill-primary:has-text('Simpan')").click()
                        screening_mandiri = ScreeningMandiri(page, format_cell_value)
                        run_screening_steps(
                            screening_mandiri, DEWASA_MANDIRI_LAKI_SCREENINGS, data, index, page
                        )
                        print(f"{Colors.BOLD}============== Skrining Mandiri Selesai =============={Colors.ENDC}")
                        print(f"{Colors.BOLD}============== Skrining Oleh Nakes Dimulai =============={Colors.ENDC}")
                        screening_nakes = ScreeningNakes(page, format_cell_value)
                        run_screening_steps(
                            screening_nakes, DEWASA_NAKES_LAKI_SCREENINGS, data, index, page
                        )
                        print(f"{Colors.BOLD}============== Skrining Oleh Nakes Selesai =============={Colors.ENDC}")
                        excel.update_status(index, "SUCCESS")
                        # page.pause()
                    elif gender == "Perempuan":
                        print(f"{Colors.OKCYAN}Skrining Perempuan Dewasa{Colors.ENDC}")
                        print(f"{Colors.BOLD}============== Skrining Mandiri Dimulai =============={Colors.ENDC}")
                        if examination_status == "Belum Pemeriksaan":
                            #butuh perbaikan di sini untuk memilih tanggal
                            page.locator("button.btn-fill-primary:has-text('Mulai Pemeriksaan')").click()
                            page.locator("button.btn-fill-primary:has-text('Simpan')").click()
                            print(f"{Colors.OKGREEN}Mulai Pemeriksaan dan Simpan berhasil diklik{Colors.ENDC}")
                        screening_mandiri = ScreeningMandiri(page, format_cell_value)
                        run_screening_steps(
                            screening_mandiri, DEWASA_MANDIRI_PEREMPUAN_SCREENINGS, data, index, page
                        )
                        print(f"{Colors.BOLD}============== Skrining Mandiri Selesai =============={Colors.ENDC}")
                        print(f"{Colors.BOLD}============== Skrining Oleh Nakes Dimulai =============={Colors.ENDC}")
                        screening_nakes = ScreeningNakes(page, format_cell_value)
                        run_screening_steps(
                            screening_nakes, DEWASA_NAKES_PEREMPUAN_SCREENINGS, data, index, page
                        )
                        print(f"{Colors.BOLD}============== Skrining Oleh Nakes Selesai =============={Colors.ENDC}")
                        excel.update_status(index, "SUCCESS")


                page.wait_for_load_state("networkidle")


            except Exception as exc:
                failed_rows.append(index)
                any_failed = True
                traceback.print_exc()
                excel.update_status(index, f"FAILED: {exc}")
                if os.getenv(DEBUG_RAISE_ERRORS_ENV) == "1":
                    raise

        context.close()
        browser.close()

    if any_failed:
        return {"status": "failed", "error_message": f"{len(failed_rows)} baris gagal diproses"}
    return {"status": "success"}


if __name__ == "__main__":
    username = os.getenv("CKG_USERNAME", "unknown")
    monitored_main(f"dewasa - {username}", main)
