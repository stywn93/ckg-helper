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
            checkbox = page.locator("input[name='noNik']")
            checkbox.set_checked(True, force=True)

            page.locator("input#nik\\ wali").fill("3512145806880002")
            page.locator('input[name="Nama Lengkap Wali"]').fill("ANNISATUL QORIAH")
            # page.pause()

            # page.locator("#Tanggal\\ Lahir .mx-input-wrapper").click()
            # page.locator('[id="Tanggal Lahir"] .mx-input-wrapper').click()
            page.locator('[id="Tanggal Lahir"] .mx-input-wrapper').filter(has_text="Pilih Tanggal Lahir").click()
            # page.locator("i.mx-icon-calendar").click()
            # page.pause()
            popup = page.locator(".mx-datepicker-popup")
            year_btn = popup.locator(".mx-btn-current-year")
            prev_year = popup.locator(".mx-btn-icon-double-left")

            while year_btn.text_content().strip() != "2008":
                prev_year.click()

            popup.locator('td.cell[title="2008-05-01"]').click()

            page.locator("div:has(> .text-gray-4:text('Pilih Jenis Kelamin'))").click()
            page.pause()
            # panel.get_by_role("button", name="25").click()
            # page.get_by_text("Pilih jenis kelamin", exact=True).click()
            page.locator(".max-h-\\[250px\\]").get_by_text("Perempuan", exact=True).click()
            # page.get_by_text("Laki-laki", exact=True).click()

            # page.locator('input#No\\ Whatsapp').fill("812345678")
            page.locator("label").filter(has_text="No. Whatsapp Wali").locator('input[name="Nomor whatsapp"]').fill(
            "81234567890")

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
