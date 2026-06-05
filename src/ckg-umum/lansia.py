import os
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


def search_patient(page, data: dict, row_number: int) -> None:
    prepare_page(page)
    # examination_status = prompt_examination_status()
    # page.locator("div.cursor-pointer.px-3").filter(has_text=examination_status).click()
    page.locator("div.cursor-pointer.px-3").filter(has_text="Sedang Pemeriksaan").click()
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



def main():
    excel_path = PROJECT_ROOT / "dataset" / "lansia.xlsx"
    username = get_required_env(USERNAME_ENV)
    password = get_required_env(PASSWORD_ENV)
    # examination_status = prompt_examination_status()
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
                search_patient(page, data, index)
                badge = page.locator("div.border-rd-full.px-3.py-1").first
                badge.wait_for(state="visible", timeout=15000)
                badge_text = badge.inner_text().strip()
                print(badge_text)
                if badge_text != "Lansia":
                    excel.update_status(index, "Gagal - ini bukan pasien lansia")
                    page.wait_for_load_state("networkidle")
                    continue

                if badge_text == "Lansia":
                    gender_locator = (
                        page.locator("div.flex.flex-col.gap-2")
                        .filter(has_text="Jenis Kelamin")
                        .locator("div.font-bold")
                    )
                    gender = gender_locator.inner_text().strip()
                    if gender == "Laki-Laki":
                        print("Skrining Laki-Laki Lansia")
                        print("============== Skrining Mandiri Dimulai ==============")
                        screening_mandiri = ScreeningMandiri(page, format_cell_value)
                        screening_mandiri.do_demografi_lansia(data, index)
                        screening_mandiri.do_risiko_kanker_usus(data, index)
                        screening_mandiri.do_risiko_tb(data, index)
                        screening_mandiri.do_hati(data, index)
                        screening_mandiri.do_keswa(data, index)
                        screening_mandiri.do_risiko_kanker_paru(data, index)
                        screening_mandiri.do_perilaku_merokok(data, index)
                        screening_mandiri.do_aktivitas_fisik(data, index)
                        print("============== Skrining Mandiri Selesai ==============")
                        print("============== Skrining Oleh Nakes Dimulai ==============")
                        screening_nakes = ScreeningNakes(page, format_cell_value)
                        screening_nakes.do_gizi_laki(data, index)
                        screening_nakes.do_gula_darah_dewasa(data, index)
                        screening_nakes.do_tekanan_darah_dewasa(data, index)
                        screening_nakes.do_skilas_penurunan_kognitif(data, index)
                        screening_nakes.do_skilas_mobilisasi(data, index)
                        screening_nakes.do_skilas_malnutrisi(data, index)
                        screening_nakes.do_skilas_depresi(data, index)
                        screening_nakes.do_gangguan_fungsional(data, index)
                        screening_nakes.do_mini_cog(data, index)
                        screening_nakes.do_ad8_ina(data, index)
                        screening_nakes.do_mobilisasi_lanjutan(data, index)
                        screening_nakes.do_malnutrisi_lanjutan(data, index)
                        screening_nakes.do_depresi_lanjutan(data, index)
                        # page.pause()
                        screening_nakes.do_risiko_tb(data, index)
                        screening_nakes.do_tb(data, index)
                        screening_nakes.do_frambusia(data, index)
                        screening_nakes.do_kusta(data, index)
                        screening_nakes.do_skabies(data, index)
                        screening_nakes.do_telinga_mata(data, index)
                        screening_nakes.do_karies(data, index)
                        screening_nakes.do_periodontal(data, index)
                        screening_nakes.do_ppok(data, index)
                        screening_nakes.do_kadar_co(data, index)
                        screening_nakes.do_lipid(data, index)
                        screening_nakes.do_fibrosis(data, index)
                        screening_nakes.do_hepatitis(data, index)
                        screening_nakes.do_fungsi_ginjal(data, index)
                        screening_nakes.do_kerusakan_ginjal(data, index)
                        screening_nakes.do_jantung(data, index)
                        screening_nakes.do_kanker_usus(data, index)
                        screening_nakes.do_kanker_paru(data, index)
                        print("============== Skrining Oleh Nakes Selesai ==============")
                        excel.update_status(index, "SUCCESS")
                        # page.pause()
                    elif gender == "Perempuan":
                        print("Skrining Perempuan Lansia")
                        print("============== Skrining Mandiri Dimulai ==============")
                        screening_mandiri = ScreeningMandiri(page, format_cell_value)
                        screening_mandiri.do_demografi_lansia(data, index)
                        screening_mandiri.do_risiko_kanker_usus(data, index)
                        screening_mandiri.do_risiko_tb(data, index)
                        screening_mandiri.do_hati(data, index)
                        screening_mandiri.do_keswa(data, index)
                        screening_mandiri.do_risiko_kanker_paru(data, index)
                        screening_mandiri.do_perilaku_merokok(data, index)
                        screening_mandiri.do_aktivitas_fisik(data, index)
                        print("============== Skrining Mandiri Selesai ==============")
                        print("============== Skrining Oleh Nakes Dimulai ==============")
                        screening_nakes = ScreeningNakes(page, format_cell_value)
                        screening_nakes.do_gizi_perempuan(data, index)
                        screening_nakes.do_gula_darah_dewasa(data, index)
                        screening_nakes.do_tekanan_darah_dewasa(data, index)
                        screening_nakes.do_skilas_penurunan_kognitif(data, index)
                        screening_nakes.do_skilas_mobilisasi(data, index)
                        screening_nakes.do_skilas_malnutrisi(data, index)
                        screening_nakes.do_skilas_depresi(data, index)
                        screening_nakes.do_gangguan_fungsional(data, index)
                        screening_nakes.do_mini_cog(data, index)
                        screening_nakes.do_ad8_ina(data, index)
                        screening_nakes.do_mobilisasi_lanjutan(data, index)
                        screening_nakes.do_malnutrisi_lanjutan(data, index)
                        screening_nakes.do_depresi_lanjutan(data, index)
                        # page.pause()
                        screening_nakes.do_risiko_tb(data, index)
                        screening_nakes.do_tb(data, index)
                        screening_nakes.do_frambusia(data, index)
                        screening_nakes.do_kusta(data, index)
                        screening_nakes.do_skabies(data, index)
                        screening_nakes.do_telinga_mata(data, index)
                        screening_nakes.do_karies(data, index)
                        screening_nakes.do_periodontal(data, index)
                        screening_nakes.do_ppok(data, index)
                        screening_nakes.do_kadar_co(data, index)
                        screening_nakes.do_lipid(data, index)
                        screening_nakes.do_fibrosis(data, index)
                        screening_nakes.do_hepatitis(data, index)
                        screening_nakes.do_fungsi_ginjal_perempuan(data, index)
                        screening_nakes.do_kerusakan_ginjal(data, index)
                        screening_nakes.do_jantung(data, index)
                        screening_nakes.do_kanker_usus(data, index)
                        screening_nakes.do_kanker_paru(data, index)
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
