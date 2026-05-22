import os
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

MONTH_LABELS = {
    "01": "Jan",
    "02": "Feb",
    "03": "Mar",
    "04": "Apr",
    "05": "Mei",
    "06": "Jun",
    "07": "Jul",
    "08": "Agu",
    "09": "Sep",
    "10": "Okt",
    "11": "Nov",
    "12": "Des",
}

def load_rows_from_excel(path: str) -> list[dict]:
    workbook = load_workbook(path)
    sheet = workbook.active

    headers = [cell.value for cell in sheet[1]]
    rows = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not any(row):
            continue
        rows.append(dict(zip(headers, row)))

    return rows

def select_date_from_picker(page, field_selector: str, date_value: str) -> None:
    year, month, day = date_value.split("-")
    month_label = MONTH_LABELS[month]

    page.locator(field_selector).click()

    popup = page.locator(".mx-datepicker-popup")
    month_btn = popup.locator(".mx-btn-current-month")
    prev_month = popup.locator(".mx-btn-icon-left")
    year_btn = popup.locator(".mx-btn-current-year")
    prev_year = popup.locator(".mx-btn-icon-double-left")

    while month_btn.text_content().strip() != month_label:
        prev_month.click()

    while year_btn.text_content().strip() != year:
        prev_year.click()

    popup.locator(f'td.cell[title="{date_value}"]').click()

def select_date_from_picker2(trigger_locator, date_value: str) -> None:
    year, month, day = date_value.split("-")
    month_label = MONTH_LABELS[month]

    trigger_locator.click()

    popup = trigger_locator.page.locator(".mx-datepicker-popup")
    month_btn = popup.locator(".mx-btn-current-month")
    prev_month = popup.locator(".mx-btn-icon-left")
    year_btn = popup.locator(".mx-btn-current-year")
    prev_year = popup.locator(".mx-btn-icon-double-left")

    while month_btn.text_content().strip() != month_label:
        prev_month.click()

    while year_btn.text_content().strip() != year:
        prev_year.click()

    popup.locator(f'td.cell[title="{date_value}"]').click()

def main():
    data_rows = load_rows_from_excel("data.xlsx")
    data = data_rows[0]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        page.goto("https://sehatindonesiaku.kemkes.go.id/login")
        page.locator("input#email").fill("asembagusjempol@gmail.com")
        page.locator("input#password").fill("Asembagus*1")

        page.pause()
        page.goto("https://sehatindonesiaku.kemkes.go.id/ckg-pendaftaran-individu")
        page.wait_for_load_state("networkidle")

        checkbox = page.locator("input[name='verify']")
        checkbox.set_checked(True, force=True)
        page.locator("button:has-text('Setuju')").click()
        page.get_by_role("button", name="Daftar Baru").click()
        nik_input = page.locator("form input#nik")
        nik_input.fill(str(data["nik"]))
        page.locator('input#Nama\\ Lengkap').fill(str(data["nama_lengkap"]))

        select_date_from_picker(page, "#Tanggal\\ Lahir .mx-input-wrapper", str(data["tgl_lahir"]))

        page.get_by_text("Pilih jenis kelamin", exact=True).click()
        page.get_by_text(str(data["gender"]), exact=True).click()

        page.locator('input#No\\ Whatsapp').fill(str(data["no_whatsapp"]))
        # page.pause()

        panel = page.locator("div:has(> .text-\\[20px\\].font-bold:text('Tanggal Pemeriksaan'))")
        # panel.get_by_role("button", str(data["tgl_pemeriksaan"])).nth(1).click()
        panel.get_by_role("button", name=str(data["tgl_pemeriksaan"])).nth(1).click()

        page.get_by_role("button", name="Selanjutnya").click()
        btn_recheck = page.locator("button:has-text('Periksa Kembali')").first
        btn_success = page.locator("button:has-text('Lanjutkan')").first
        try:
            btn_recheck.wait_for(state="visible", timeout=3000)
            btn_recheck.click()
            btn_recheck.wait_for(state="hidden", timeout=5000)
            checkbox = page.locator("input[name='noNik']")
            checkbox.set_checked(True, force=True)
            page.locator("input#nik\\ wali").fill(str(data["nik_wali"]))
            page.locator('input[name="Nama Lengkap Wali"]').fill(str(data["nama_wali"]))

            page.locator('[id="Tanggal Lahir"] .mx-input-wrapper').filter(has_text="Pilih Tanggal Lahir").click()

            select_date_from_picker2(page.locator('[id="Tanggal Lahir"] .mx-input-wrapper').filter(has_text="Pilih Tanggal Lahir"),str(data["tgl_lahir_wali"])
            )

            page.locator("div:has(> .text-gray-4:text('Pilih Jenis Kelamin'))").click()
            page.locator(".max-h-\\[250px\\]").get_by_text(str(data["gender_wali"]), exact=True).click()
            page.locator("label").filter(has_text="No. Whatsapp Wali").locator('input[name="Nomor whatsapp"]').fill(
            str(data["no_whatsapp_wali"]))
            page.get_by_role("button", name="Selanjutnya").click()
            page.locator("button:has-text('Lanjutkan')").click()
            # page.pause()

        except PlaywrightTimeoutError:
            btn_success.click()

        page.get_by_text("Pilih status pernikahan", exact=True).click()
        page.get_by_text(str(data["pernikahan"]), exact=True).click()

        page.get_by_text("Pilih pekerjaan", exact=True).click()
        page.get_by_text(str(data["pekerjaan"]), exact=True).click()

        page.get_by_text("Pilih alamat domisili", exact=True).click()
        page.get_by_text(str(data["prov"]), exact=True).click()
        page.get_by_text(str(data["kab"]), exact=True).click()
        page.get_by_text(str(data["kec"]), exact=True).click()
        page.get_by_text(str(data["desa"]), exact=True).click()

        page.locator("textarea#detail-domisili").fill(str(data["domisili"]))

        page.get_by_role("button", name="Selanjutnya").click()
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Daftarkan Tanpa NIK").click()
        page.wait_for_timeout(1500)
        # page.get_by_role("button", name="Selanjutnya").click()
        page.wait_for_load_state("networkidle")
        page.get_by_role("button", name="Bantu Isi Skrining Mandiri").click()
        page.wait_for_timeout(1500)
        page.wait_for_load_state("networkidle")
        checkbox = page.locator("input[id='sameLocation']")
        checkbox.set_checked(True, force=True)
        page.wait_for_timeout(2000)
        page.get_by_role("button", name="Simpan").click()

        page.pause()

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
