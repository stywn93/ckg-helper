import os
import traceback
import re

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
        if is_success_status(row_data.get(STATUS_COLUMN)):
            skipped_success_rows.append(row_number)
            continue
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
    page.locator("#sq_103i_list [role='option']").filter(
        has_text=format_cell_value(data["aktivitas_pekerjaan"])).click()
    if data["aktivitas_pekerjaan"] == "Ya":
        page.locator("input[aria-labelledby='sq_104_ariaTitle']").fill(
            format_cell_value(data["hari_pekerjaan"])
        )
        page.locator("input[aria-labelledby='sq_105_ariaTitle']").fill(
            format_cell_value(data["menit_pekerjaan"])
        )

    page.locator("div[aria-controls='sq_106i_list']").click()
    page.locator("#sq_106i .sd-dropdown__value").click()
    page.locator("#sq_106i_list [role='option']").filter(
        has_text=format_cell_value(data["aktivitas_perjalanan"])).click()
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


# ---------- Pelayanan Oleh Nakes ------------

def centang_pemeriksaan(page, data: dict, row_number: int) -> None:
    print("Centang Pemeriksaan")
    daftar_pemeriksaan = [
        # Gizi Tekanan Darah dan Gula Darah Laki-laki
        ("input#hasil-lab-0-0", format_cell_value(data["periksa_gizi_laki"]), False),
        ("input#hasil-lab-0-1", format_cell_value(data["periksa_gula_darah"]), False),
        ("input#hasil-lab-0-2", format_cell_value(data["periksa_tensi"]), False),
        # TB Nakes Dewasa Dan Lansia
        ("input#hasil-lab-1-0", format_cell_value(data["periksa_risiko_tbc"]), False),
        ("input#hasil-lab-1-1", format_cell_value(data["periksa_tbc"]), False),
        # Tropis Terabaikan
        ("input#hasil-lab-2-0", format_cell_value(data["periksa_frambusia"]), False),
        ("input#hasil-lab-2-1", format_cell_value(data["periksa_kusta"]), False),
        ("input#hasil-lab-2-2", format_cell_value(data["periksa_skabies"]), False),
        # Telinga dan Mata
        ("input#hasil-lab-3-0", format_cell_value(data["periksa_telinga_mata"]), False),
        # Gigi Dewasa
        ("input#hasil-lab-4-0", format_cell_value(data["periksa_karies"]), False),
        ("input#hasil-lab-4-1", format_cell_value(data["periksa_periodontal"]), False),
        # PPOK
        ("input#hasil-lab-5-0", format_cell_value(data["periksa_ppok"]), False),
        # Tata laksana Merokok
        ("input#hasil-lab-6-0", format_cell_value(data["periksa_co"]), False),
        # Laboratorium
        ("input#hasil-lab-7-0", format_cell_value(data["periksa_lipid"]), False),
        ("input#hasil-lab-7-1", format_cell_value(data["periksa_fibrosis"]), False),
        ("input#hasil-lab-7-2", format_cell_value(data["periksa_hepatitis"]), False),
        ("input#hasil-lab-7-3", format_cell_value(data["periksa_fungsi_ginjal"]), False),
        ("input#hasil-lab-7-4", format_cell_value(data["periksa_kerusakan_ginjal"]), False),
        # EKG
        ("input#hasil-lab-8-0", format_cell_value(data["periksa_jantung"]), False),
        # Kanker Usus
        ("input#hasil-lab-9-0", format_cell_value(data["periksa_kanker_usus"]), False),
        # Kanker Paru
        ("input#hasil-lab-10-0", format_cell_value(data["periksa_kanker_paru"]), False),
        # Catin
        ("input#hasil-lab-11-0", format_cell_value(data["periksa_hiv"]), False),
        ("input#hasil-lab-11-0", format_cell_value(data["periksa_sifilis"]), False),
    ]

    for selector, checked, pause in daftar_pemeriksaan:
        print("Selector ", selector)
        checkbox = page.locator(selector)
        if checked is False and checkbox.is_checked():
            print("if condition 1")
            checkbox.click(force=True)
            page.get_by_role("button", name="Tidak Periksa").click()
        else:
            page.locator(selector).set_checked(checked, force=True)

        if pause:
            page.pause()
    print("Centang Pemeriksaan Selesai")

def do_pemeriksaan_check(page, selector: str, checked: bool) -> None:
    checkbox = page.locator(selector)
    if checked is False and checkbox.is_checked():
        print("status pemeriksaan is False")
        checkbox.click(force=True)
        page.get_by_role("button", name="Tidak Periksa").click()
    elif checked is True:
        print("status pemeriksaan is True")
        print("selector ", selector)
        # page.pause()
        checkbox.click()
        # page.locator(selector).set_checked(checked, force=True)

def do_gizi_laki(page, data: dict, row_number: int) -> None:
    print("Skrining Gizi Laki dimulai")
    #butuh perbaikan di sini, seharusnya sebelum klik tombol Input Data, pastikan sudah centang Diperiksa agar bisa diklik
    do_pemeriksaan_check(page, "input#hasil-lab-0-0", True)
    page.locator('[id="rowfrm000093"]').click()

    page.locator("input[aria-labelledby='sq_100_ariaTitle']").fill(format_cell_value(data["berat_badan"]))
    page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(format_cell_value(data["tinggi_badan"]))
    page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(format_cell_value(data["lingkar_perut"]))
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Gizi Laki selesai")

def do_gula_darah_dewasa(page, data: dict, row_number: int) -> None:
    print("Skrining Gula Darah Dewasa dimulai")
    do_pemeriksaan_check(page, "input#hasil-lab-0-1", True)
    page.locator('[id="rowfrm000256"]').click()
    page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        has_text=format_cell_value(data["pernah_diabetes"])
    ).click()
    if(data["pernah_diabetes"] == "Ya"):
        page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
            format_cell_value(data["total_bulan_diabetes"])
        )
    page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
        format_cell_value(data["gula_darah_sewaktu"])
    )
    if (data["pernah_diabetes"] == "Tidak"):
        page.locator("input[aria-labelledby='sq_103_ariaTitle']").fill(
            format_cell_value(data["gula_darah_sewaktu_2"])
        )
    page.locator("input[aria-labelledby='sq_104_ariaTitle']").fill(
        format_cell_value(data["gula_darah_puasa"])
    )
    page.locator("input[aria-labelledby='sq_105_ariaTitle']").fill(
        format_cell_value(data["gula_darah_pp"])
    )
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Gula Darah Dewasa selesai")

def do_tekanan_darah_dewasa(page, data: dict, row_number: int) -> None:
    print("Skrining Tekanan Darah Dewasa dimulai")
    do_pemeriksaan_check(page, "input#hasil-lab-0-2", True)
    page.locator('[id="rowfrm000265"]').click()
    page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        has_text=format_cell_value(data["pernah_hipertensi"])
    ).click()
    if(data["pernah_hipertensi"] == "Ya"):
        page.locator("input[aria-labelledby='sq_101_ariaTitle']").fill(
            format_cell_value(data["total_bulan_hipertensi"])
        )
    page.locator("input[aria-labelledby='sq_102_ariaTitle']").fill(
        format_cell_value(data["sistolik"])
    )
    page.locator("input[aria-labelledby='sq_103_ariaTitle']").fill(
        format_cell_value(data["diastolik"])
    )
    page.locator("input[aria-labelledby='sq_104_ariaTitle']").fill(
        format_cell_value(data["sistolik_2"])
    )
    page.locator("input[aria-labelledby='sq_105_ariaTitle']").fill(
        format_cell_value(data["diastolik_2"])
    )
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Tekanan Darah Dewasa selesai")

def do_risiko_tb(page, data: dict, row_number: int) -> None:
    print("Skrining Risiko TB dimulai")
    do_pemeriksaan_check(page, "input#hasil-lab-1-0", True)
    page.locator('[id="rowfrm000182"]').click()
    page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
        has_text=format_cell_value(data["pernah_batuk_tidak_sembuh"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
        has_text=format_cell_value(data["bb_turun"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_102_ariaTitle'] label").filter(
        has_text=format_cell_value(data["demam_hilang_timbul"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_103_ariaTitle'] label").filter(
        has_text=format_cell_value(data["berkeringat_malam"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_104_ariaTitle'] label").filter(
        has_text=format_cell_value(data["pembesaran_getah_bening"])
    ).click()
    page.locator("fieldset[aria-labelledby='sq_105_ariaTitle'] label").filter(
        has_text=format_cell_value(data["radiografi_toraks"])
    ).click()
    if(data["radiografi_toraks"] == "Ya"):
        value = format_cell_value(data["hasil_rontgen"])
        page.locator(
            "fieldset[aria-labelledby='sq_106_ariaTitle'] label"
        ).filter(
            has_text=re.compile(rf"^{re.escape(value)}$")
        ).click()

    page.locator("input:has-text('Kirim')").click()
    print("Skrining Risiko TB selesai")
    # page.pause()

def do_tb(page, data: dict, row_number: int) -> None:
    print("Skrining TB dimulai")
    do_pemeriksaan_check(page, "label[for='hasil-lab-1-1']", True)
    page.locator('[id="rowfrm000184"]').click()

    page.locator("div[aria-controls='sq_100i_list']").click()
    page.locator("#sq_100i_list [role='option']").filter(has_text=format_cell_value(data["kontak_tbc"])).click()
    if data["kontak_tbc"] == "Riwayat kontak serumah" or data["kontak_tbc"] == "Riwayat kontak erat":
        page.locator("fieldset[aria-labelledby='sq_101_ariaTitle'] label").filter(
            has_text=format_cell_value(data["jenis_tbc"])
        ).click()
    page.locator("div[aria-controls='sq_102i_list']").click()
    page.locator("#sq_102i_list [role='option']").filter(has_text=format_cell_value(data["metode_pemeriksaan_tbc"])).click()
    if data["metode_pemeriksaan_tbc"] == "TCM":
        page.locator("div[aria-controls='sq_103i_list']").click()
        page.locator("#sq_103i_list [role='option']").filter(
            has_text=format_cell_value(data["hasil_pemeriksaan_tbc"])).click()
    elif data["metode_pemeriksaan_tbc"] == "BTA":
        page.locator("div[aria-controls='sq_104i_list']").click()
        page.locator("#sq_104i_list [role='option']").filter(
            has_text=format_cell_value(data["hasil_pemeriksaan_tbc"])).click()
    elif data["metode_pemeriksaan_tbc"] == "NPOC":
        page.locator("div[aria-controls='sq_105i_list']").click()
        page.locator("#sq_105i_list [role='option']").filter(
            has_text=format_cell_value(data["hasil_pemeriksaan_tbc"])).click()
    page.pause()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining TB selesai")

def do_frambusia(page, data: dict, row_number: int) -> None:
    print("Skrining Frambusia dimulai")
    page.locator('[id="rowfrm000199"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Frambusia selesai")

def do_kusta(page, data: dict, row_number: int) -> None:
    print("Skrining Kusta dimulai")
    page.locator('[id="rowfrm000198"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Kusta selesai")

def do_skabies(page, data: dict, row_number: int) -> None:
    print("Skrining Skabies dimulai")
    page.locator('[id="rowfrm000201"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Skabies selesai")

def do_telinga_mata(page, data: dict, row_number: int) -> None:
    print("Skrining Telinga dan Mata dimulai")
    page.locator('[id="rowfrm000099"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Telinga dan Mata selesai")

def do_karies(page, data: dict, row_number: int) -> None:
    print("Skrining Karies dimulai")
    page.locator('[id="rowfrm000055"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Karies selesai")

def do_periodontal(page, data: dict, row_number: int) -> None:
    print("Skrining Periodontal dimulai")
    page.locator('[id="rowfrm000056"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Periodontal selesai")

def do_ppok(page, data: dict, row_number: int) -> None:
    print("Skrining PPOK dimulai")
    page.locator('[id="rowfrm000101"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining PPOK selesai")

def do_kadar_co(page, data: dict, row_number: int) -> None:
    print("Skrining Kadar CO dimulai")
    page.locator('[id="rowfrm000186"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Kadar CO selesai")

def do_lipid(page, data: dict, row_number: int) -> None:
    print("Skrining Lipid dimulai")
    page.locator('[id="rowfrm000047"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Lipid selesai")

def do_fibrosis(page, data: dict, row_number: int) -> None:
    print("Skrining Fibrosis dimulai")
    page.locator('[id="rowfrm000045"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Fibrosis selesai")

def do_hepatitis(page, data: dict, row_number: int) -> None:
    print("Skrining Hepatitis dimulai")
    page.locator('[id="rowfrm000044"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Hepatitis selesai")

def do_fungsi_ginjal(page, data: dict, row_number: int) -> None:
    print("Skrining Fungsi Ginjal dimulai")
    page.locator('[id="rowfrm000244"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Fungsi Ginjal selesai")

def do_kerusakan_ginjal(page, data: dict, row_number: int) -> None:
    print("Skrining Kerusakan Ginjal dimulai")
    page.locator('[id="rowfrm000248"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Kerusakan Ginjal selesai")

def do_jantung(page, data: dict, row_number: int) -> None:
    print("Skrining Jantung dimulai")
    page.locator('[id="rowfrm000057"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Jantung selesai")

def do_kanker_usus(page, data: dict, row_number: int) -> None:
    print("Skrining Kanker Usus dimulai")
    page.locator('[id="rowfrm000050"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Kanker Usus selesai")

def do_kanker_paru(page, data: dict, row_number: int) -> None:
    print("Skrining Kanker Paru dimulai")
    page.locator('[id="rowfrm000041"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Kanker Paru selesai")

def do_hiv(page, data: dict, row_number: int) -> None:
    print("Skrining HIV dimulai")
    page.locator('[id="rowfrm000188"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining HIV selesai")

def do_sifilis(page, data: dict, row_number: int) -> None:
    print("Skrining Sifilis dimulai")
    page.locator('[id="rowfrm000191"]').click()
    page.pause()
    # page.locator("fieldset[aria-labelledby='sq_100_ariaTitle'] label").filter(
    #     has_text=format_cell_value(data["batuk_tidak_sembuh"])
    # ).click()
    page.locator("input:has-text('Kirim')").click()
    print("Skrining Sifilis selesai")

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
                # do_aktivitas_fisik(page, data, index)
                # centang_pemeriksaan(page, data, index)
                # do_gizi_laki(page, data, index)
                # do_gula_darah_dewasa(page, data, index)
                # do_tekanan_darah_dewasa(page, data, index)
                # do_risiko_tb(page, data, index)
                do_tb(page, data, index)
                page.pause()

                # page.pause()
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
