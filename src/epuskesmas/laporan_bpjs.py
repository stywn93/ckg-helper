import getpass
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

PROJECT_ROOT = Path(os.getenv("CKG_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
load_dotenv(PROJECT_ROOT / ".env")

EPUSKESMAS_URL_ENV = "EPUSKESMAS_URL"
EPUSKESMAS_USERNAME_ENV = "EPUSKESMAS_USERNAME"
EPUSKESMAS_PASSWORD_ENV = "EPUSKESMAS_PASSWORD"
LOGIN_TIMEOUT_MS = int(os.getenv("EPUSKESMAS_LOGIN_TIMEOUT_MS", "120000"))


def get_epuskesmas_credentials() -> tuple[str, str, str]:
    url = os.getenv(EPUSKESMAS_URL_ENV, "").strip()
    username = os.getenv(EPUSKESMAS_USERNAME_ENV, "").strip()
    password = os.getenv(EPUSKESMAS_PASSWORD_ENV, "").strip()

    if not url:
        print("\n[Konfigurasi ePuskesmas]")
        url = input("Masukkan URL ePuskesmas (misal: https://situbondo.epuskesmas.id): ").strip()
    while not username:
        username = input("Username ePuskesmas: ").strip()
    while not password:
        password = getpass.getpass("Password ePuskesmas: ").strip()

    # Simpan kembali ke .env jika belum tersimpan
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith(f"{EPUSKESMAS_URL_ENV}="):
                new_lines.append(f"{EPUSKESMAS_URL_ENV}={url}")
                updated = True
            elif line.startswith(f"{EPUSKESMAS_USERNAME_ENV}="):
                new_lines.append(f"{EPUSKESMAS_USERNAME_ENV}={username}")
                updated = True
            elif line.startswith(f"{EPUSKESMAS_PASSWORD_ENV}="):
                new_lines.append(f"{EPUSKESMAS_PASSWORD_ENV}={password}")
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            new_lines.extend([
                "",
                "# Konfigurasi ePuskesmas",
                f"{EPUSKESMAS_URL_ENV}={url}",
                f"{EPUSKESMAS_USERNAME_ENV}={username}",
                f"{EPUSKESMAS_PASSWORD_ENV}={password}",
            ])
        env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    os.environ[EPUSKESMAS_URL_ENV] = url
    os.environ[EPUSKESMAS_USERNAME_ENV] = username
    os.environ[EPUSKESMAS_PASSWORD_ENV] = password

    return url, username, password


def run():
    url, username, password = get_epuskesmas_credentials()

    # Pastikan URL langsung mengarah ke endpoint /login
    login_url = url.rstrip("/")
    if not login_url.endswith("/login"):
        login_url += "/login"

    with sync_playwright() as playwright:
        user_data_dir = PROJECT_ROOT / "browsers" / "epuskesmas_profile"
        user_data_dir.mkdir(parents=True, exist_ok=True)

        launch_kwargs = {
            "user_data_dir": str(user_data_dir),
            "headless": False,
            "ignore_default_args": ["--enable-automation"],
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        }

        try:
            # Gunakan Google Chrome lokal agar lolos verifikasi Cloudflare
            context = playwright.chromium.launch_persistent_context(channel="chrome", **launch_kwargs)
        except Exception:
            # Fallback ke Chromium default jika Chrome tidak ditemukan
            context = playwright.chromium.launch_persistent_context(**launch_kwargs)

        page = context.pages[0] if context.pages else context.new_page()

        # Sembunyikan tanda otomasi navigator.webdriver dari script bot detection
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"\n1. Membuka langsung halaman login: {login_url}...")
        page.goto(login_url, wait_until="domcontentloaded")

        print("2. Mengisi username & password...")
        email_field = page.get_by_role("textbox", name="E-mail / No. HP / ID")
        email_field.wait_for(state="visible", timeout=15000)
        email_field.fill(username)

        password_field = page.get_by_role("textbox", name="kata kunci")
        password_field.wait_for(state="visible", timeout=15000)
        password_field.fill(password)

        print("\n>>> Silakan verifikasi captcha di browser dan klik tombol Login! <<<")
        print("Menunggu login selesai (maks 120 detik)...")

        try:
            page.wait_for_url(lambda current_url: current_url != login_url, timeout=LOGIN_TIMEOUT_MS)
            print("\n✓ Login berhasil terdeteksi! Halaman saat ini:", page.url)
        except PlaywrightTimeoutError:
            print("\n[Warning] Timeout menunggu perpindahan halaman login.")

        input("\nTekan Enter di terminal ini untuk menutup browser...")
        context.close()


if __name__ == "__main__":
    run()
