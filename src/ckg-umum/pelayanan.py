import os
import traceback

from dotenv import load_dotenv
from openpyxl import load_workbook
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from playwright_window_layout import launch_chromium_with_layout, pause_with_inspector_layout

load_dotenv()

STATUS_COLUMN = "status"
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


def is_success_status(value) -> bool:
    return str(value).strip().upper() == "SUCCESS"


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} belum diisi.")
    return value


def load_rows_from_excel(path: str) -> tuple:
    workbook = load_workbook(path)
    sheet = workbook.active

    headers = [cell.value for cell in sheet[1]]
    if STATUS_COLUMN not in headers:
        sheet.cell(row=1, column=len(headers) + 1, value=STATUS_COLUMN)
        headers.append(STATUS_COLUMN)

    rows = []
    skipped_success_rows = []
    empty_rows = 0

    for row_number, row in enumerate(
        sheet.iter_rows(min_row=2, values_only=True), start=2
    ):
        if not any(row):
            empty_rows += 1
            continue
        row_data = dict(zip(headers, row))
        # skip pengecekan status dulu
        # if is_success_status(row_data.get(STATUS_COLUMN)):
        #     skipped_success_rows.append(row_number)
        #     continue
        rows.append({"row_number": row_number, "data": row_data})

    summary = {
        "empty_rows": empty_rows,
        "skipped_success_rows": skipped_success_rows,
        "total_data_rows": sheet.max_row - 1,
    }

    return workbook, sheet, headers, rows, summary

def format_cell_value(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)


def update_row_status(
    workbook, sheet, headers: list, excel_path: str, row_number: int, status: str
) -> None:
    status_column_index = headers.index(STATUS_COLUMN) + 1
    sheet.cell(row=row_number, column=status_column_index, value=status)
    workbook.save(excel_path)


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
    print("end of prepare_page")


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
    print("end of search_patient")


def do_demografi_dewasa(page, data: dict, row_number: int) -> None:
    print("do demografi dewasa started")
    page.locator('[id="rowfrm000006"]').click()
    # soal 1
    page.locator("label").filter(
        has_text=format_cell_value(data["status_perkawinan"])
    ).click()
    # jika soal 1 jawabannya selain menikah, maka klik ini
    if data["status_perkawinan"] != "Menikah":
        page.locator("label").filter(
            has_text=format_cell_value(data["rencana_menikah"])
        ).click()

    # soal 2 atau 3
    page.locator("label").filter(
        has_text=format_cell_value(data["disabilitas"])
    ).click()
    page.locator("input:has-text('Kirim')").click()

    print("end of do_pemeriksaan")


def do_risiko_kanker_usus(page, data: dict, row_number: int) -> None:
    print("do risiko kanker usus started")
    page.locator('[id="rowfrm000027"]').click()
    page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        has_text=format_cell_value(data["keluarga_kanker_usus"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
        has_text=format_cell_value(data["merokok"])
    ).click()
    page.locator("input:has-text('Kirim')").click()
    print("end of risiko kanker usus")


def do_risiko_tb(page, data: dict, row_number: int) -> None:
    print("do risiko tb started")
    page.locator('[id="rowfrm000180"]').click()
    page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        has_text=format_cell_value(data["batuk_tidak_sembuh"])
    ).click()
    page.locator("input:has-text('Kirim')").click()
    print("end of do risiko tb")


def do_hati(page, data: dict, row_number: int) -> None:
    print("do hati started")
    page.locator('[id="rowfrm000028"]').click()
    page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        has_text=format_cell_value(data["hepatitis_b"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
        has_text=format_cell_value(data["ibu_hepatitis_b"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
        has_text=format_cell_value(data["seks_bukan_pasangan"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
        has_text=format_cell_value(data["transfusi_darah"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
        has_text=format_cell_value(data["hemodialisis"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
        has_text=format_cell_value(data["pengguna_narkoba"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
        has_text=format_cell_value(data["odhiv"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
        has_text=format_cell_value(data["hepatitis_c"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_108_ariaTitle'] label").filter(
        has_text=format_cell_value(data["kolesterol_tinggi"])
    ).click()
    page.locator("input:has-text('Kirim')").click()
    print("end of do hati")


def do_keswa(page, data: dict, row_number: int) -> None:
    print("do keswa started")
    page.locator('[id="rowfrm000067"]').click()
    page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        has_text=format_cell_value(data["tidak_bersemangat"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
        has_text=format_cell_value(data["merasa_tertekan"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
        has_text=format_cell_value(data["gugup_cemas"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
        has_text=format_cell_value(data["khawatir"])
    ).click()
    page.locator("input:has-text('Kirim')").click()
    print("end of do keswa")


def do_risiko_kanker_paru(page, data: dict, row_number: int) -> None:
    print("do risiko kanker paru started")
    page.locator('[id="rowfrm000138"]').click()
    page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        has_text=format_cell_value(data["merokok_setahun_terakhir"])
    ).click()
    if data["merokok_setahun_terakhir"] == "Tidak":
        page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=format_cell_value(data["merokok_15_tahun"])
        ).click()
        page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
            has_text=format_cell_value(data["terpapar_rokok"])
        ).click()
        page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
            has_text=format_cell_value(data["kanker_paru_keluarga"])
        ).click()
        page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=format_cell_value(data["gejala_batuk"])
        ).click()
        page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
            has_text=format_cell_value(data["tbc"])
        ).click()

    page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
        has_text=format_cell_value(data["terpapar_rokok"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
        has_text=format_cell_value(data["kanker_paru_keluarga"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
        has_text=format_cell_value(data["gejala_batuk"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
        has_text=format_cell_value(data["tbc"])
    ).click()
    page.locator("input:has-text('Kirim')").click()
    print("end of risiko kanker paru")


def do_perilaku_merokok(page, data: dict, row_number: int) -> None:
    print("do perilaku merokok started")
    page.locator('[id="rowfrm000064"]').click()
    page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        has_text=format_cell_value(data["merokok_setahun_terakhir_b"])
    ).click()

    if data["merokok_setahun_terakhir_b"] == "Ya":
        page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=format_cell_value(data["jenis_rokok"])
        ).click()
        page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
            format_cell_value(data["berapa_tahun"])
        )
        page.locator("input[aria-labelledby='sq_103_ariaTitle']").fill(
            format_cell_value(data["berapa_batang"])
        )

    elif data["merokok_setahun_terakhir_b"] == "Tidak":
        page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
            has_text=format_cell_value(data["pernah_merokok"])
        ).click()
        if data["pernah_merokok"] == "Ya":
            page.locator("input[aria-labelledby='sq_105_ariaTitle']").fill(
                format_cell_value(data["berapa_tahun_sebelumnya"])
            )
            page.locator("fieldset[aria-labelledby='sq_106_ariaTitle'] label").filter(
                has_text=format_cell_value(data["kapan_berhenti"])
            ).click()
    page.locator("fieldset[aria-labelledby='sq_107_ariaTitle'] label").filter(
        has_text=format_cell_value(data["terpapar_sebulan_terakhir"])
    ).click()
    page.locator("input:has-text('Kirim')").click()
    print("end of do perilaku merokok")


def do_aktivitas_fisik(page, data: dict, row_number: int) -> None:
    print("do aktivitas fisik started")
    page.locator('[id="rowfrm000169"]').click()

    page.locator("div[aria-controls='sq_100i_list']").click()
    page.locator("#sq_100i_list [role='option']").filter(has_text=format_cell_value(data["aktivitas_domestik"])).click()
    if data["aktivitas_domestik"] == "Ya":
        page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
            format_cell_value(data["hari_domestik"])
        )
        page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
            format_cell_value(data["menit_domestik"])
        )

    page.locator("div[aria-controls='sq_103i_list']").click()
    page.locator("#sq_103i .sd-dropdown__value").click()
    page.locator("#sq_103i_list [role='option']").filter(has_text=format_cell_value(data["aktivitas_pekerjaan"])).click()
    if data["aktivitas_pekerjaan"] == "Ya":
        page.locator("input[aria-labelledby='sq_104_ariaTitle']").fill(
            format_cell_value(data["hari_pekerjaan"])
        )
        page.locator("input[aria-labelledby='sq_105_ariaTitle']").fill(
            format_cell_value(data["menit_pekerjaan"])
        )

    page.locator("div[aria-controls='sq_106i_list']").click()
    page.locator("#sq_106i .sd-dropdown__value").click()
    page.locator("#sq_106i_list [role='option']").filter(has_text=format_cell_value(data["aktivitas_perjalanan"])).click()
    if data["aktivitas_perjalanan"] == "Ya":
        page.locator("input[aria-labelledby='sq_107_ariaTitle']").fill(
            format_cell_value(data["hari_perjalanan"])
        )
        page.locator("input[aria-labelledby='sq_108_ariaTitle']").fill(
            format_cell_value(data["menit_perjalanan"])
        )

    page.locator("div[aria-controls='sq_109i_list']").click()
    page.locator("#sq_109i .sd-dropdown__value").click()
    page.locator("#sq_109i_list [role='option']").filter(
        has_text=format_cell_value(data["aktivitas_olahraga"])).click()
    if data["aktivitas_olahraga"] == "Ya":
        page.locator("input[aria-labelledby='sq_110_ariaTitle']").fill(
            format_cell_value(data["hari_olahraga"])
        )
        page.locator("input[aria-labelledby='sq_111_ariaTitle']").fill(
            format_cell_value(data["menit_olahraga"])
        )

    page.locator("div[aria-controls='sq_112i_list']").click()
    page.locator("#sq_112i .sd-dropdown__value").click()

    page.locator("#sq_112i_list [role='option']").filter(
        has_text=format_cell_value(data["aktivitas_kerja_berat"])).click()
    if data["aktivitas_kerja_berat"] == "Ya":
        page.locator("input[aria-labelledby='sq_113_ariaTitle']").fill(
            format_cell_value(data["hari_kerja_berat"])
        )
        page.locator("input[aria-labelledby='sq_114_ariaTitle']").fill(
            format_cell_value(data["menit_kerja_berat"])
        )

    page.locator("div[aria-controls='sq_115i_list']").click()
    page.locator("#sq_115i .sd-dropdown__value").click()
    page.locator("#sq_115i_list [role='option']").filter(
        has_text=format_cell_value(data["aktivitas_olahraga_berat"])).click()
    if data["aktivitas_olahraga_berat"] == "Ya":
        page.locator("input[aria-labelledby='sq_116_ariaTitle']").fill(
            format_cell_value(data["hari_olahraga_berat"])
        )
        page.locator("input[aria-labelledby='sq_117_ariaTitle']").fill(
            format_cell_value(data["menit_olahraga_berat"])
        )
    page.locator("input:has-text('Kirim')").click()
    print("end of do aktivitas fisik")


def main():
    excel_path = "dataset/pelayanan.xlsx"
    username = get_required_env(USERNAME_ENV)
    password = get_required_env(PASSWORD_ENV)
    # examination_status = prompt_examination_status()
    workbook, sheet, headers, data_rows, excel_summary = load_rows_from_excel(
        excel_path
    )
    if not data_rows:
        skipped_success_rows = excel_summary["skipped_success_rows"]
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
                update_row_status(
                    workbook, sheet, headers, excel_path, index, "SUCCESS"
                )
                # do_demografi_dewasa(page, data, index)
                # do_risiko_kanker_usus(page, data, index)
                # do_risiko_tb(page, data, index)
                # do_hati(page, data, index)
                # do_keswa(page, data, index)
                # do_risiko_kanker_paru(page, data, index)
                # do_perilaku_merokok(page, data, index)
                do_aktivitas_fisik(page, data, index)
                update_row_status(
                    workbook, sheet, headers, excel_path, index, "SUCCESS"
                )
            except Exception as exc:
                failed_rows.append(index)
                traceback.print_exc()
                update_row_status(
                    workbook, sheet, headers, excel_path, index, f"FAILED: {exc}"
                )
                if os.getenv(DEBUG_RAISE_ERRORS_ENV) == "1":
                    raise

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
