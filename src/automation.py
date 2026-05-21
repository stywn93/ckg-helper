import os

from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


def main():



    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 1. Buka halaman login dan isi kredensial otomatis
        page.goto("https://sehatindonesiaku.kemkes.go.id/login")
        page.locator("input#email").fill("asembagusjempol@gmail.com")
        page.locator("input#password").fill("Asembagus*1")

        page.pause()
        # 3. Setelah persetujuan, lanjut ke halaman pendaftaran
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
        prev_year = popup.locator(".mx-btn-icon-double-left")

        while year_btn.text_content().strip() != "2010":
            prev_year.click()

        popup.locator('td.cell[title="2010-05-01"]').click()

        page.get_by_text("Pilih jenis kelamin", exact=True).click()
        page.get_by_text("Laki-laki", exact=True).click()

        page.locator('input#No\\ Whatsapp').fill("812345678")

        panel = page.locator("div:has(> .text-\\[20px\\].font-bold:text('Tanggal Pemeriksaan'))")
        panel.get_by_role("button", name="25").click()

        page.get_by_role("button", name="Selanjutnya").click()
        btn_recheck = page.locator("button:has-text('Periksa Kembali')").first
        try:
        # Tunggu popup muncul
            btn_recheck.wait_for(state="visible", timeout=3000)
            # Klik tombol "Periksa Kembali" untuk menutup popup
            btn_recheck.click()
            # Tunggu popup benar-benar hilang
            btn_recheck.wait_for(state="hidden", timeout=5000)
        except PlaywrightTimeoutError:
            # Popup tidak muncul = NIK valid, lanjut ke step berikutnya
            pass


        # 4. Tunggu halaman load sempurna

        # 5. Klik tombol Daftar Baru
        #
        #
        #
        # # Isi NIK dulu untuk cek validasi. Checkbox "tidak punya NIK" hanya dipakai jika NIK ditolak.
        # nik_input = page.locator("form input#nik")
        # nik_input.fill("1234567890123456")
        # page.locator('input#Nama\\ Lengkap').fill("Budi Santoso")
        # page.locator("#Tanggal\\ Lahir .mx-input-wrapper").click()
        #
        # popup = page.locator(".mx-datepicker-popup")
        # year_btn = popup.locator(".mx-btn-current-year")
        # prev_year = popup.locator(".mx-btn-icon-double-left")
        #
        # while year_btn.text_content().strip() != "1990":
        #     prev_year.click()
        #
        # popup.locator('td.cell[title="2010-05-01"]').click()
        #
        # page.get_by_text("Pilih jenis kelamin", exact=True).click()
        # page.get_by_text("Laki-laki", exact=True).click()
        #
        # page.locator('input#No\\ Whatsapp').fill("812345678")
        #
        # panel = page.locator("div:has(> .text-\\[20px\\].font-bold:text('Tanggal Pemeriksaan'))")
        # panel.get_by_role("button", name="25").click()
        #
        # page.get_by_role("button", name="Selanjutnya").click()

        # btn_recheck = page.locator("button:has-text('Periksa Kembali')").first
        # try:
        #     # Tunggu popup muncul
        #     btn_recheck.wait_for(state="visible", timeout=3000)
        #     # Klik tombol "Periksa Kembali" untuk menutup popup
        #     btn_recheck.click()
        #     # Tunggu popup benar-benar hilang
        #     btn_recheck.wait_for(state="hidden", timeout=5000)
        # except PlaywrightTimeoutError:
        #     # Popup tidak muncul = NIK valid, lanjut ke step berikutnya
        #     pass
        

        # Lanjutkan automasi di sini...
        page.pause()  # pause lagi untuk observasi

        browser.close()

if __name__ == "__main__":
    main()
