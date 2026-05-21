from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 1. Buka halaman login
        page.goto("https://sehatindonesiaku.kemkes.go.id/login")

        # 2. Tunggu kamu login manual + selesaikan captcha
        #    Skrip akan PAUSE di sini sampai kamu tekan tombol ▶ di browser
        page.pause()

        # 3. Setelah kamu tekan ▶, langsung navigasi ke halaman tujuan
        page.goto("https://sehatindonesiaku.kemkes.go.id/ckg-pendaftaran-individu")

        # 4. Tunggu halaman load sempurna
        page.wait_for_load_state("networkidle")

        # 5. Klik tombol Daftar Baru
        page.get_by_role("button", name="Daftar Baru").click()

        #klik field nik
        page.locator("form input#nik").fill("1234567890123456")

        # Lanjutkan automasi di sini...
        page.pause()  # pause lagi untuk observasi

        browser.close()

if __name__ == "__main__":
    main()