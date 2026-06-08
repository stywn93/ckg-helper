import os
import inspect
import traceback
import re
import sys
from pathlib import Path

HELPERS_DIR = Path(__file__).resolve().parents[1] / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))
PROJECT_ROOT = Path(__file__).resolve().parents[2]

from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from playwright_window_layout import launch_chromium_with_layout, pause_with_inspector_layout

# coba gunakan helper
from excel import ExcelStatusWorkbook, format_cell_value
from screening_mandiri import ScreeningMandiri
from screening_nakes import ScreeningNakes
load_dotenv(PROJECT_ROOT / ".env")

USERNAME_ENV = "CKG_USERNAME"
PASSWORD_ENV = "CKG_PASSWORD"
DEBUG_RAISE_ERRORS_ENV = "CKG_DEBUG_RAISE_ERRORS"
SCREENING_UI_TIMEOUT_MS = int(os.getenv("CKG_SCREENING_UI_TIMEOUT_MS", "2000"))
EXAMINATION_STATUS_OPTIONS = {
    "1": "Belum Pemeriksaan",
    "2": "Sedang Pemeriksaan",
    "3": "Selesai Pemeriksaan",
}
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
CHILD_MANDIRI_SCREENINGS = [
    "do_demografi_anak",
]
CHILD_NAKES_SCREENINGS = [
    "do_riwayat_imunisasi_hepatitis_b",
    "do_berat_lahir",
    "do_jantung_bawaan",
    "do_darah_tumit",
    "do_shk",
    "do_konfirmasi_shk",
    "do_gizi_laki",
    "do_pertumbuhan_balita",
    "do_kpsp",
    "do_m_chat_1",
    "do_m_chat_2",
    "do_risiko_tb_anak",
    "do_tb_anak",
    "do_frambusia",
    "do_kusta",
    "do_skabies",
    "do_telinga_mata_anak",
    "do_periksa_gigi_anak",
]

def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} belum diisi.")
    return value


def prompt_examination_status() -> str:
    print("Pilih status pemeriksaan:")
    for option_number, option_label in EXAMINATION_STATUS_OPTIONS.items():
        print(f"{option_number}. {option_label}")

    while True:
        selected_option = input("Masukkan nomor pilihan (1-3): ").strip()
        if selected_option in EXAMINATION_STATUS_OPTIONS:
            return EXAMINATION_STATUS_OPTIONS[selected_option]
        print("Pilihan tidak valid. Masukkan nomor 1, 2, atau 3.")


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


def search_patient(page, data: dict, row_number: int) -> str:
    prepare_page(page)
    examination_status = prompt_examination_status()
    page.locator("div.cursor-pointer.px-3").filter(has_text=examination_status).click()
    # page.locator("div.cursor-pointer.px-3").filter(has_text="Sedang Pemeriksaan").click()
    page.locator("div.mx-input-wrapper").click()
    batas_awal = format_cell_value(data["batas_awal"])
    batas_akhir = format_cell_value(data["batas_akhir"])
    page.locator(f'td.cell[title="{batas_awal}"]').click()
    page.locator(f'td.cell[title="{batas_akhir}"]').click()

    page.locator("span:has-text('Nama')").click()
    page.get_by_text("Nama", exact=True).nth(0).click()
    page.locator("input#searchNik").fill(format_cell_value(data["nama"]))
    page.keyboard.press("Enter")
    page.wait_for_load_state("networkidle")
    page.locator("button:has-text('Mulai')").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)
    for remaining_seconds in range(3, 0, -1):
        print(f"Menunggu halaman pemeriksaan tampil... {remaining_seconds} detik")
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
            print(f"Skip {method_name}: function tidak ditemukan.")
            continue

        if not is_screening_form_available(page, method):
            print(
                f"Skip {method_name}: elemen UI form tidak ditemukan "
                f"dalam {SCREENING_UI_TIMEOUT_MS} ms."
            )
            continue

        try:
            print(f"Menjalankan {method_name}")
            method(data, row_number)
            page.wait_for_load_state("networkidle")
        except PlaywrightTimeoutError as exc:
            print(f"Skip {method_name}: elemen UI tidak ditemukan atau tidak tampil. Detail: {exc}")
            close_active_screening_form(page)


def main():
    excel_path = PROJECT_ROOT / "dataset" / "anak.xlsx"
    username = get_required_env(USERNAME_ENV)
    password = get_required_env(PASSWORD_ENV)

    excel = ExcelStatusWorkbook(excel_path)
    data_rows = excel.pending_rows()
    if not data_rows:
        skipped_success_rows = excel.summary["skipped_success_rows"]
        if skipped_success_rows:
            print(
                "Tidak ada data yang perlu diproses. "
                f"Baris {skipped_success_rows} dilewati karena status sudah SUCCESS."
            )
            print("Kosongkan kolom status untuk memproses ulang baris tersebut.")
        else:
            print("Tidak ada data pada file Excel.")
            print("")
        return

    with sync_playwright() as p:
        browser, window_layout = launch_chromium_with_layout(p)
        context = browser.new_context(no_viewport=True)
        context.set_default_timeout(30000)  # 30 detik untuk locator click/fill/wait_for/inner_text
        context.set_default_navigation_timeout(30000)  # 30 detik untuk goto/load/navigation
        page = context.new_page()

        page.goto("https://sehatindonesiaku.kemkes.go.id/ckg-pelayanan")
        page.locator("input#email").fill(username)
        page.locator("input#password").fill(password)
        pause_with_inspector_layout(page, window_layout)

        failed_rows = []

        for row_entry in data_rows:
            index = row_entry["row_number"]
            data = row_entry["data"]
            try:
                examination_status = search_patient(page, data, index)
                badge = page.locator("div.border-rd-full.px-3.py-1").first
                badge.wait_for(state="visible", timeout=15000)
                badge_text = badge.inner_text().strip()
                print(badge_text)
                if badge_text != "Bayi Balita":
                    excel.update_status(index, f"Gagal - ini bukan pasien Bayi Balita. Ini adalah pasien {badge_text}")
                    page.wait_for_load_state("networkidle")
                    continue

                if badge_text == "Bayi Balita":
                    gender_locator = (
                        page.locator("div.flex.flex-col.gap-2")
                        .filter(has_text="Jenis Kelamin")
                        .locator("div.font-bold")
                    )
                    gender = gender_locator.inner_text().strip()
                    if gender == "Laki-Laki":
                        print("Skrining Laki-Laki Bayi Balita")
                        print("============== Skrining Mandiri Dimulai ==============")
                        # sebelum mulai skrining seharusnya klik Mulai Pemeriksaan dahulu, jika tombol tersebut tidak ditemukan maka skip jangan error. Caranya dengan cara mengecek prompt_examination_status yang paling ideal
                        if examination_status == "Belum Pemeriksaan":
                            #butuh perbaikan di sini untuk memilih tanggal
                            page.locator("button.btn-fill-primary:has-text('Mulai Pemeriksaan')").click()
                            page.locator("button.btn-fill-primary:has-text('Simpan')").click()
                        # page.pause()
                        screening_mandiri = ScreeningMandiri(page, format_cell_value)
                        run_screening_steps(screening_mandiri, CHILD_MANDIRI_SCREENINGS, data, index, page)
                        print("============== Skrining Mandiri Selesai ==============")
                        print("============== Skrining Oleh Nakes Dimulai ==============")
                        screening_nakes = ScreeningNakes(page, format_cell_value)
                        run_screening_steps(screening_nakes, CHILD_NAKES_SCREENINGS, data, index, page)
                        print("============== Skrining Oleh Nakes Selesai ==============")
                        excel.update_status(index, "SUCCESS")
                        # page.pause()
                    elif gender == "Perempuan":
                        print("Skrining Perempuan Bayi Balita")
                        print("============== Skrining Mandiri Dimulai ==============")
                        screening_mandiri = ScreeningMandiri(page, format_cell_value)
                        run_screening_steps(screening_mandiri, CHILD_MANDIRI_SCREENINGS, data, index, page)
                        print("============== Skrining Mandiri Selesai ==============")
                        print("============== Skrining Oleh Nakes Dimulai ==============")
                        screening_nakes = ScreeningNakes(page, format_cell_value)
                        run_screening_steps(screening_nakes, CHILD_NAKES_SCREENINGS, data, index, page)
                        print("============== Skrining Oleh Nakes Selesai ==============")
                        excel.update_status(index, "SUCCESS")


                page.wait_for_load_state("networkidle")


            except Exception as exc:
                failed_rows.append(index)
                traceback.print_exc()
                excel.update_status(index, f"FAILED: {exc}")
                if os.getenv(DEBUG_RAISE_ERRORS_ENV) == "1":
                    raise

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
