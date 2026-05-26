import os

from dotenv import load_dotenv
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

load_dotenv()

STATUS_COLUMN = "status"
USERNAME_ENV = "CKG_USERNAME"
PASSWORD_ENV = "CKG_PASSWORD"
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

    for row_number, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
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


def set_date_range(page, field_selector: str, date_value: str) -> None:
    page.pause()
    year, month, day = date_value.split("-")
    target_year = int(year)
    target_month = int(month)
    month_label = MONTH_LABELS[month]
    print("parsing date success")
    page.pause()
    page.locator(field_selector).click()
    print("click success")
    popup = page.locator(".mx-datepicker-popup")
    month_btn = popup.locator(".mx-btn-current-month")
    prev_month = popup.locator(".mx-btn-icon-left")
    next_month = popup.locator(".mx-btn-icon-right")
    year_btn = popup.locator(".mx-btn-current-year")
    prev_year = popup.locator(".mx-btn-icon-double-left")

    while int(year_btn.text_content().strip()) != year:
        current_year = int(year_btn.text_content().strip())
        if target_year < current_year:
            prev_year.click()
        else:
            break

    a = 1
    while True:
        current_label = month_btn.text_content().strip()
        if current_label == month_label:
            break

        current_month = int(MONTH_TO_NUMBER[current_label])
        a += 1

        if target_month < current_month:
            prev_month.click()
        else:
            next_month.click()

        page.wait_for_timeout(300)

    popup.locator(f'td.cell[title="{date_value}"]').click()

def format_cell_value(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)

def update_row_status(workbook, sheet, headers: list, excel_path: str, row_number: int, status: str) -> None:
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
        # page.pause()
        page.locator("button:has-text('Simpan')").click()
        page.wait_for_load_state("networkidle")
    print("end of prepare_page")


def search_patient(page, data: dict, row_number: int, examination_status: str) -> None:
    prepare_page(page)
    page.locator("div.cursor-pointer.px-3").filter(has_text=examination_status).click()
    page.locator("div.mx-input-wrapper").click()
    batas_awal = format_cell_value(data["batas_awal"])
    batas_akhir = format_cell_value(data["batas_akhir"])
    page.locator(f'td.cell[title="{batas_awal}"]').click()
    page.locator(f'td.cell[title="{batas_akhir}"]').click()

    page.locator("span:has-text('Nama')").click()
    page.get_by_text("Nama", exact=True).nth(0).click()
    page.locator('input#searchNik').fill(format_cell_value(data["nama"]))
    page.keyboard.press("Enter")
    page.wait_for_load_state("networkidle")
    page.locator("button:has-text('Mulai')").first.click()
    page.wait_for_load_state("networkidle")
    print("end of search_patient")

def do_demografi_dewasa(page, data: dict, row_number: int) -> None:
    print("do demografi dewasa started")
    page.locator('[id="rowfrm000006"]').click()
    # soal 1
    page.locator("label").filter(has_text=format_cell_value(data["status_perkawinan"])).click()
    # jika soal 1 jawabannya selain menikah, maka klik ini
    # page.locator('[id="sq_101i_0"]').check()
    if data["status_perkawinan"] != "Menikah":
        page.locator("label").filter(has_text=format_cell_value(data["rencana_menikah"])).click()
    # page.locator('[id="sq_100i_0"]').check()


    # soal 2 atau 3
    page.locator("label").filter(has_text=format_cell_value(data["disabilitas"])).click()
    # page.locator('[id="sq_102i_0"]').check()
    page.locator("input:has-text('Kirim')").click()
    # page.pause()

    print("end of do_pemeriksaan")
    page.pause()


def main():
    excel_path = "dataset/pelayanan.xlsx"
    username = get_required_env(USERNAME_ENV)
    password = get_required_env(PASSWORD_ENV)
    examination_status = prompt_examination_status()
    workbook, sheet, headers, data_rows, excel_summary = load_rows_from_excel(excel_path)
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
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        page.goto("https://sehatindonesiaku.kemkes.go.id/ckg-pelayanan")
        page.locator("input#email").fill(username)
        page.locator("input#password").fill(password)
        page.pause()

        failed_rows = []

        for row_entry in data_rows:
            index = row_entry["row_number"]
            data = row_entry["data"]
            try:
                search_patient(page, data, index, examination_status)
                update_row_status(workbook, sheet, headers, excel_path, index, "SUCCESS")
                do_demografi_dewasa(page, data, index)
                update_row_status(workbook, sheet, headers, excel_path, index, "SUCCESS")
            except Exception as exc:
                failed_rows.append(index)
                update_row_status(workbook, sheet, headers, excel_path, index, f"FAILED: {exc}")
                # print(f"Baris Excel {index} gagal diproses: {exc}")

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
