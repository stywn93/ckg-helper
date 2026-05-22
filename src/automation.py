import os

from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError



def main():

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
        nik_input.fill("1234567890123456")
        page.locator('input#Nama\\ Lengkap').fill("Budi Santoso")
        page.locator("#Tanggal\\ Lahir .mx-input-wrapper").click()

        popup = page.locator(".mx-datepicker-popup")
        year_btn = popup.locator(".mx-btn-current-year")
        month_btn = popup.locator(".mx-btn-current-month")
        prev_year = popup.locator(".mx-btn-icon-double-left")
        prev_month = popup.locator(".mx-btn-icon-left")

        while month_btn.text_content().strip() != "Okt":
            prev_month.click()

        while year_btn.text_content().strip() != "2010":
            prev_year.click()


        # page.pause()

        popup.locator('td.cell[title="2010-10-01"]').click()

        page.get_by_text("Pilih jenis kelamin", exact=True).click()
        page.get_by_text("Laki-laki", exact=True).click()

        page.locator('input#No\\ Whatsapp').fill("812345678")

        panel = page.locator("div:has(> .text-\\[20px\\].font-bold:text('Tanggal Pemeriksaan'))")
        panel.get_by_role("button", name="25").click()

        page.get_by_role("button", name="Selanjutnya").click()
        btn_recheck = page.locator("button:has-text('Periksa Kembali')").first
        btn_success = page.locator("button:has-text('Lanjutkan')").first
        try:
            btn_recheck.wait_for(state="visible", timeout=3000)
            btn_recheck.click()
            btn_recheck.wait_for(state="hidden", timeout=5000)
            checkbox = page.locator("input[name='noNik']")
            checkbox.set_checked(True, force=True)
            page.locator("input#nik\\ wali").fill("3512052205820001")
            page.locator('input[name="Nama Lengkap Wali"]').fill("KUSYONO")

            page.locator('[id="Tanggal Lahir"] .mx-input-wrapper').filter(has_text="Pilih Tanggal Lahir").click()
            popup = page.locator(".mx-datepicker-popup")
            month_btn = popup.locator(".mx-btn-current-month")
            prev_month = popup.locator(".mx-btn-icon-left")
            year_btn = popup.locator(".mx-btn-current-year")
            prev_year = popup.locator(".mx-btn-icon-double-left")
            while month_btn.text_content().strip() != "Mei":
                prev_month.click()
            while year_btn.text_content().strip() != "1982":
                prev_year.click()
            popup.locator('td.cell[title="1982-05-22"]').click()

            page.locator("div:has(> .text-gray-4:text('Pilih Jenis Kelamin'))").click()
            page.locator(".max-h-\\[250px\\]").get_by_text("Laki-laki", exact=True).click()
            page.locator("label").filter(has_text="No. Whatsapp Wali").locator('input[name="Nomor whatsapp"]').fill(
            "81234567890")
            page.get_by_role("button", name="Selanjutnya").click()
            page.locator("button:has-text('Lanjutkan')").click()

        except PlaywrightTimeoutError:
            btn_success.click()

        page.get_by_text("Pilih status pernikahan", exact=True).click()
        page.get_by_text("Belum Menikah", exact=True).click()

        page.get_by_text("Pilih pekerjaan", exact=True).click()
        page.get_by_text("Pegawai Swasta ", exact=True).click()

        page.get_by_text("Pilih alamat domisili", exact=True).click()
        page.get_by_text("Jawa Timur ", exact=True).click()
        page.get_by_text("Kab. Situbondo ", exact=True).click()
        page.get_by_text("Kendit ", exact=True).click()
        page.get_by_text("Balung ", exact=True).click()

        page.locator("textarea#detail-domisili").fill("Jl. ABCD")

        page.get_by_role("button", name="Selanjutnya").click()
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Daftarkan Tanpa NIK").click()
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Selanjutnya").click()
        page.wait_for_load_state("networkidle")
        page.get_by_role("button", name="Tutup").click()

        page.pause()

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
