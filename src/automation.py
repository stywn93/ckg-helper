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

        # 2. Captcha tetap manual. Setelah user login berhasil, halaman persetujuan akan muncul.
        verify_checkbox = page.locator("input#verify")
        verify_checkbox.wait_for(state="attached", timeout=180000)
        verify_checkbox.scroll_into_view_if_needed()
        verify_checkbox.evaluate(
            """el => {
                el.checked = true;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.click();
            }"""
        )
        page.locator("button:has-text('Setuju')").click()
        page.wait_for_load_state("networkidle")

        # 3. Setelah persetujuan, lanjut ke halaman pendaftaran
        page.goto("https://sehatindonesiaku.kemkes.go.id/ckg-pendaftaran-individu")

        # 4. Tunggu halaman load sempurna
        page.wait_for_load_state("networkidle")

        # 5. Klik tombol Daftar Baru
        page.get_by_role("button", name="Daftar Baru").click()

        #klik field nik
        page.locator("form input#nik").fill("1234567890123456")
        page.locator('input#Nama\\ Lengkap').fill("Budi Santoso")
        page.locator("#Tanggal\\ Lahir .mx-input-wrapper").click()

        popup = page.locator(".mx-datepicker-popup")
        year_btn = popup.locator(".mx-btn-current-year")
        prev_year = popup.locator(".mx-btn-icon-double-left")

        while year_btn.text_content().strip() != "1990":
            prev_year.click()

        popup.locator('td.cell[title="1990-05-15"]').click()

        page.get_by_text("Pilih jenis kelamin", exact=True).click()
        page.get_by_text("Laki-laki", exact=True).click()

        page.locator('input#No\\ Whatsapp').fill("812345678")

        panel = page.locator("div:has(> .text-\\[20px\\].font-bold:text('Tanggal Pemeriksaan'))")
        panel.get_by_role("button", name="25").click()

        page.get_by_role("button", name="Selanjutnya").click()

        btn_recheck = page.locator("button:has-text('Periksa Kembali')").first
        try:
            btn_recheck.wait_for(state="visible", timeout=3000)
            page.locator("input#tidak-punya-nik").check()
        except PlaywrightTimeoutError:
            pass

        

        # Lanjutkan automasi di sini...
        page.pause()  # pause lagi untuk observasi

        browser.close()

if __name__ == "__main__":
    main()
