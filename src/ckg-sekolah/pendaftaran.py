import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


HELPERS_DIR = Path(__file__).resolve().parents[1] / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

CKU_DIR = Path(__file__).resolve().parent.parent / "ckg-umum"
if str(CKU_DIR) not in sys.path:
    sys.path.insert(0, str(CKU_DIR))

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import click_delay  # noqa: F401
from playwright_window_layout import launch_chromium_with_layout

from date_picker import DatePicker
from excel import ExcelStatusWorkbook, ExcelAppendWorkbook, format_cell_value, resolve_dataset
from custom_exceptions import SkipRowException
from api_report import monitored_main
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

PROJECT_ROOT = Path(os.getenv("CKG_PROJECT_ROOT", Path(__file__).resolve().parents[2]))

load_dotenv(PROJECT_ROOT / ".env")

USERNAME_ENV = "CKG_USERNAME"
PASSWORD_ENV = "CKG_PASSWORD"
LOGIN_SUCCESS_TIMEOUT_MS = int(os.getenv("CKG_LOGIN_SUCCESS_TIMEOUT_MS", "60000"))

def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} belum diisi.")
    return value


def prepare_registration_page(page) -> None:
    page.goto("https://sehatindonesiaku.kemkes.go.id/ckg-pendaftaran-anak-sekolah")
    page.wait_for_load_state("networkidle")
    page.reload(wait_until="networkidle")

    checkbox = page.locator("input[name='verify']")
    if checkbox.count() > 0:
        print("mencari checkbox verifikasi...")
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== checkbox verifikasi ditemukan{Colors.ENDC}")
        print("mencoba mengklik checkbox...")
        checkbox.set_checked(True, force=True)
        print("mencari tombol setuju...")
        setuju = page.locator("button:has-text('Setuju')")
        if setuju.count() > 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol setuju ditemukan{Colors.ENDC}")
            setuju.click()
            page.wait_for_load_state("networkidle")

    print("mencari tombol daftar baru...")
    daftar_baru = page.get_by_role("button", name="Daftar Baru")
    if daftar_baru.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol daftar baru ditemukan{Colors.ENDC}")
        daftar_baru.click()


def login_and_wait_for_profile(page, username: str, password: str) -> None:
    page.goto("https://sehatindonesiaku.kemkes.go.id/login")
    page.locator("input#email").fill(username)
    page.locator("input#password").fill(password)

    submit_button = page.locator("button[type='submit']").first
    if submit_button.count() > 0:
        submit_button.click()
    else:
        page.keyboard.press("Enter")

    try:
        page.wait_for_url(
            re.compile(r".*/profile(?:[/?#].*)?$"),
            timeout=LOGIN_SUCCESS_TIMEOUT_MS,
        )
        page.wait_for_load_state("networkidle")
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(
            "Login belum berhasil: halaman tidak redirect ke /profile "
            f"dalam {LOGIN_SUCCESS_TIMEOUT_MS} ms. URL saat ini: {page.url}"
        ) from exc

def wait_for_first_visible(page, locators_dict, timeout=5000):
    """
    Waits for the first element in the dict to become visible.
    Returns the key of the element that became visible.
    """
    start_time = time.time()
    while time.time() - start_time < (timeout / 1000):
        for key, locator in locators_dict.items():
            if locator.is_visible():
                return key
        time.sleep(0.5)
    raise PlaywrightTimeoutError("None of the expected buttons appeared")

# def handle_periksa_kembali(page, data: dict, date_picker: DatePicker) -> None:
#     btn_recheck = page.locator("button:has-text('Periksa Kembali')").first
#     btn_success = page.locator("button:has-text('Lanjutkan')").first
#     try:
#         btn_recheck.wait_for(state="visible", timeout=3000)
#         btn_recheck.click()
#         btn_recheck.wait_for(state="hidden", timeout=3000)
#         checkbox = page.locator("input[name='noNik']")
#         checkbox.set_checked(True, force=True)
#         page.locator("input#nik\\ wali").fill(format_cell_value(data["nik_wali"]))
#         page.locator('input[name="Nama Lengkap Wali"]').fill(format_cell_value(data["nama_wali"]))

#         date_picker.select(
#             page.locator('[id="Tanggal Lahir"] .mx-input-wrapper').filter(has_text="Pilih Tanggal Lahir"),
#             format_cell_value(data["tgl_lahir_wali"]),
#         )

#         page.locator("div:has(> .text-gray-4:text('Pilih Jenis Kelamin'))").click()
#         page.locator(".max-h-\\[250px\\]").get_by_text(format_cell_value(data["gender_wali"]), exact=True).click()
#         page.locator("label").filter(has_text="No. Whatsapp Wali").locator('input[name="Nomor whatsapp"]').fill(
#             format_cell_value(data["no_whatsapp_wali"])
#         )
#         page.get_by_role("button", name="Selanjutnya").click()
#         page.locator("button:has-text('Lanjutkan')").click()

#     except PlaywrightTimeoutError:
#         btn_success.click()

def handle_periksa_kembali(page, data: dict, date_picker: DatePicker) -> None:
    print("mencari input nama lengkap...")
    nama_lengkap = page.locator('input#Nama\\ Lengkap')
    if nama_lengkap.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== input nama lengkap ditemukan{Colors.ENDC}")
        print(f"nama lengkap di excel : {format_cell_value(data['nama_lengkap'])}")
        nama_lengkap.fill(format_cell_value(data["nama_lengkap"]))

    print("mencari field tanggal lahir...")
    tanggal_lahir = page.locator("#Tanggal\\ Lahir .mx-input-wrapper")
    if tanggal_lahir.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field tanggal lahir ditemukan{Colors.ENDC}")
        print(f"tanggal lahir di excel : {format_cell_value(data['tgl_lahir'])}")
        date_picker.select(tanggal_lahir, format_cell_value(data["tgl_lahir"]))

    print("mencari field jenis kelamin...")
    jenis_kelamin = page.locator("div:nth-child(5) > div > .relative > .m-auto > .icon")
    if jenis_kelamin.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field jenis kelamin ditemukan{Colors.ENDC}")
        jenis_kelamin.click()
        pilihan_jenis_kelamin = page.locator("div.absolute.top-13.z-2000").get_by_text(
            format_cell_value(data["gender"]), exact=True
        )
        if pilihan_jenis_kelamin.count() > 0:
            print(f"jenis kelamin di excel : {format_cell_value(data['gender'])}")
            pilihan_jenis_kelamin.click()

    print("mencari nomor whatsapp...")
    no_whatsapp = page.locator('input#No\\ Whatsapp')
    if no_whatsapp.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== nomor whatsapp ditemukan{Colors.ENDC}")
        print(f"nomor whatsapp di excel : {format_cell_value(data['no_whatsapp'])}")
        no_whatsapp.fill(format_cell_value(data["no_whatsapp"]))

    # Select a specific day button by exact day number (avoids "1" matching "11", "12"...)
    # dob = datetime.strptime(format_cell_value(data['tgl_lahir']), "%Y-%m-%d")

def isi_data_wali(page, data: dict, date_picker: DatePicker) -> None:
    print("mencari input NIK wali...")
    nik_wali = page.get_by_role("textbox", name="NIK *")
    if nik_wali.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== input NIK wali ditemukan{Colors.ENDC}")
        print(f"NIK wali di excel : {format_cell_value(data['nik_wali'])}")
        nik_wali.click()
        nik_wali.fill(format_cell_value(data["nik_wali"]))

    print("mencari input nama wali...")
    nama_wali = page.locator("[id=\"Nama Lengkap-wali\"]")
    if nama_wali.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== input nama wali ditemukan{Colors.ENDC}")
        print(f"nama wali di excel : {format_cell_value(data['nama_wali'])}")
        nama_wali.click()
        nama_wali.fill(format_cell_value(data["nama_wali"]))

    print("mencari field tanggal lahir wali...")
    tanggal_lahir_wali = page.locator('[id="Tanggal Lahir-wali"]').locator(".mx-datepicker")
    if tanggal_lahir_wali.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field tanggal lahir wali ditemukan{Colors.ENDC}")
        print(f"tanggal lahir wali di excel : {format_cell_value(data['tgl_lahir_wali'])}")
        tanggal_lahir_wali.click()
        date_picker.select(tanggal_lahir_wali, format_cell_value(data["tgl_lahir_wali"]))

    print("mencari field jenis kelamin wali...")
    jenis_kelamin_wali = page.locator("div:has(> .text-gray-4:text('Pilih Jenis Kelamin'))")
    if jenis_kelamin_wali.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field jenis kelamin wali ditemukan{Colors.ENDC}")
        jenis_kelamin_wali.click()
        pilihan_jenis_kelamin_wali = page.locator(".max-h-\\[250px\\]").get_by_text(
            format_cell_value(data["gender_wali"]), exact=True
        )
        if pilihan_jenis_kelamin_wali.count() > 0:
            print(f"jenis kelamin wali di excel : {format_cell_value(data['gender_wali'])}")
            pilihan_jenis_kelamin_wali.click()

    print("mencari nomor whatsapp wali...")
    no_whatsapp_wali = page.locator('[id="No whatsapp-wali"]')
    if no_whatsapp_wali.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== nomor whatsapp wali ditemukan{Colors.ENDC}")
        print(f"nomor whatsapp wali di excel : {format_cell_value(data['no_whatsapp_wali'])}")
        no_whatsapp_wali.fill(format_cell_value(data["no_whatsapp_wali"]))

def register_single_entry(page, data: dict, row_number: int, date_picker: DatePicker) -> None:
    prepare_registration_page(page)
    print()
    print(f"{Colors.BOLD}======================={Colors.ENDC}")
    print(f"{Colors.OKBLUE}Nama : {format_cell_value(data['nama_lengkap'])}{Colors.ENDC}")

    print("mencari input NIK...")
    nik_input = page.locator("form input#nik")
    if nik_input.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== input NIK ditemukan{Colors.ENDC}")
        print(f"NIK di excel : {format_cell_value(data['nik'])}")
        nik_input.fill(format_cell_value(data["nik"]))

    print("mencari input nama lengkap...")
    nama_lengkap = page.locator('input#Nama\\ Lengkap')
    if nama_lengkap.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== input nama lengkap ditemukan{Colors.ENDC}")
        print(f"nama lengkap di excel : {format_cell_value(data['nama_lengkap'])}")
        nama_lengkap.fill(format_cell_value(data["nama_lengkap"]))

    print("mencari field tanggal lahir...")
    tanggal_lahir = page.locator("#Tanggal\\ Lahir .mx-input-wrapper")
    if tanggal_lahir.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field tanggal lahir ditemukan{Colors.ENDC}")
        print(f"tanggal lahir di excel : {format_cell_value(data['tgl_lahir'])}")
        date_picker.select(tanggal_lahir, format_cell_value(data["tgl_lahir"]))

    print("mencari field jenis kelamin...")
    jenis_kelamin = page.get_by_text("Pilih jenis kelamin", exact=True)
    if jenis_kelamin.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field jenis kelamin ditemukan{Colors.ENDC}")
        jenis_kelamin.click()
        pilihan_jenis_kelamin = page.locator("div.absolute.top-13.z-2000").get_by_text(
            format_cell_value(data["gender"]), exact=True
        )
        if pilihan_jenis_kelamin.count() > 0:
            print(f"jenis kelamin di excel : {format_cell_value(data['gender'])}")
            pilihan_jenis_kelamin.click()

    print("mencari nomor whatsapp...")
    no_whatsapp = page.locator('input#No\\ Whatsapp')
    if no_whatsapp.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== nomor whatsapp ditemukan{Colors.ENDC}")
        print(f"nomor whatsapp di excel : {format_cell_value(data['no_whatsapp'])}")
        no_whatsapp.fill(format_cell_value(data["no_whatsapp"]))

    # Select a specific day button by exact day number (avoids "1" matching "11", "12"...)
    dob = datetime.strptime(format_cell_value(data['tgl_lahir']), "%Y-%m-%d")
    today = datetime.now(ZoneInfo("Asia/Jakarta"))

    # Raw day difference
    # if diff > 21915 or diff < 2191 then do isi data wali
    diff = today.date() - dob.date()
    # print(f"Total days: {diff.days}")

    day = datetime.now().day
    # day = 7
    # day_button = page.locator("button").filter(
    #     has=page.locator("span.font-bold", has_text=re.compile(rf"^{day}$"))
    # )
    # day_button.click()
    if diff.days > 21915 or diff.days < 2191:
        print("try to call isi data wali")
        isi_data_wali(page, data, date_picker)

    print("mencari tombol selanjutnya...")
    selanjutnya = page.get_by_role("button", name="Selanjutnya")
    if selanjutnya.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol selanjutnya ditemukan{Colors.ENDC}")
        selanjutnya.click()
    # page.pause()
    # ayah ini ke mana??? 



    # Opsi 1 jika sudah menerima CKG
    # Opsi 2 jika belum menerima CKG
    locators = {
        "quota_habis" : page.get_by_role("button", name="Lanjut", exact=True),
        "cari_individu": page.get_by_role("button", name="Cari Individu", exact=True), #jika sudah menerima CKG
        "lanjutkan": page.get_by_role("button", name="Lanjutkan", exact=True), #jika NIK valid dan belum menerima CKG
        "periksa_kembali": page.get_by_role("button", name="Periksa Kembali", exact=True), #jika NIK tidak valid
    }

    found = wait_for_first_visible(page, locators)
    print(f"Button locators yang ditemukan: {found}")
    # page.pause()
    if found == "quota_habis":
        print("Quota Pemeriksaan habis")
        print("mencari tombol lanjut...")
        if locators["quota_habis"].count() > 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol lanjut ditemukan{Colors.ENDC}")
            locators["quota_habis"].click()
        # page.pause()
        next_found = wait_for_first_visible(page, locators)
        print(f"next_found : {next_found}")
        if next_found == "periksa_kembali":
            print("mencari tombol periksa kembali...")
            if locators["periksa_kembali"].count() > 0:
                print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol periksa kembali ditemukan{Colors.ENDC}")
                locators["periksa_kembali"].click()
            print("mencari checkbox tidak punya NIK...")
            no_nik = page.locator("input#tidak-punya-nik[type='checkbox']")
            if no_nik.count() > 0:
                print(f"{Colors.OKGREEN}{Colors.BOLD}=== checkbox tidak punya NIK ditemukan{Colors.ENDC}")
                no_nik.click(force=True)
            handle_periksa_kembali(page, data, date_picker)
            isi_data_wali(page, data, date_picker)
            print("mencari tombol selanjutnya...")
            selanjutnya = page.get_by_role("button", name="Selanjutnya", exact=True)
            if selanjutnya.count() > 0:
                print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol selanjutnya ditemukan{Colors.ENDC}")
                selanjutnya.click()
            next_found_2 = wait_for_first_visible(page, locators)
            if(next_found_2 == "quota_habis"):
                print("mencari tombol lanjut...")
                if locators["quota_habis"].count() > 0:
                    print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol lanjut ditemukan{Colors.ENDC}")
                    locators["quota_habis"].click()
                next_found_3 = wait_for_first_visible(page, locators)
                if(next_found_3 == "lanjutkan"):
                    print("mencari tombol lanjutkan...")
                    if locators["lanjutkan"].count() > 0:
                        print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol lanjutkan ditemukan{Colors.ENDC}")
                        locators["lanjutkan"].click()
            elif next_found_2 == "lanjutkan":
                print("mencari tombol lanjutkan...")
                if locators["lanjutkan"].count() > 0:
                    print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol lanjutkan ditemukan{Colors.ENDC}")
                    locators["lanjutkan"].click()
        elif next_found == "cari_individu":
            print(f"{Colors.WARNING}pasien ini sudah menerima CKG{Colors.ENDC}")
            raise SkipRowException("Pasien ini sudah menerima CKG")
        elif next_found == "lanjutkan":
            locators["lanjutkan"].click()
        # print(f"next_found {next_found}")
    elif found == "periksa_kembali":
        print("mencari tombol periksa kembali...")
        if locators["periksa_kembali"].count() > 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol periksa kembali ditemukan{Colors.ENDC}")
            locators["periksa_kembali"].click()
        print("mencari checkbox tidak punya NIK...")
        no_nik = page.locator("input#tidak-punya-nik[type='checkbox']")
        if no_nik.count() > 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}=== checkbox tidak punya NIK ditemukan{Colors.ENDC}")
            no_nik.click(force=True)
        handle_periksa_kembali(page, data, date_picker)
        # page.pause()
        isi_data_wali(page, data, date_picker)
        print("mencari tombol selanjutnya...")
        selanjutnya = page.get_by_role("button", name="Selanjutnya", exact=True)
        if selanjutnya.count() > 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol selanjutnya ditemukan{Colors.ENDC}")
            selanjutnya.click()
        next_found = wait_for_first_visible(page, locators)
        if next_found == "lanjutkan":
            print("mencari tombol lanjutkan...")
            if locators["lanjutkan"].count() > 0:
                print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol lanjutkan ditemukan{Colors.ENDC}")
                locators["lanjutkan"].click()
    elif found == "cari_individu":
        print(f"{Colors.WARNING}pasien ini sudah menerima CKG{Colors.ENDC}")
        raise SkipRowException("Pasien ini sudah menerima CKG")
    else:
        print(f"{Colors.WARNING}pasien belum menerima CKG{Colors.ENDC}")
        print("mencari tombol lanjutkan...")
        lanjutkan = page.get_by_role("button", name="Lanjutkan", exact=True)
        if lanjutkan.count() > 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol lanjutkan ditemukan{Colors.ENDC}")
            lanjutkan.click()

    print("mencari field status pernikahan...")
    status_pernikahan = page.get_by_text("Pilih status pernikahan", exact=True)
    if status_pernikahan.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field status pernikahan ditemukan{Colors.ENDC}")
        status_pernikahan.click()
        pilihan_status = page.get_by_text(format_cell_value(data["pernikahan"]), exact=True)
        if pilihan_status.count() > 0:
            print(f"status pernikahan di excel : {format_cell_value(data['pernikahan'])}")
            pilihan_status.click()

    print("mencari field penyandang disabilitas...")
    disabilitas = page.get_by_text("Pilih penyandang disabilitas", exact=True)
    if disabilitas.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field penyandang disabilitas ditemukan{Colors.ENDC}")
        disabilitas.click()
        pilihan_disabilitas = page.get_by_text(format_cell_value(data["disabilitas"]), exact=True)
        if pilihan_disabilitas.count() > 0:
            print(f"disabilitas di excel : {format_cell_value(data['disabilitas'])}")
            pilihan_disabilitas.click()

    #jika NIK ditemukan maka tidak perlu mengisi pekerjaan
    if found != "lanjutkan":
        print("mencari field pekerjaan...")
        pekerjaan = page.get_by_text("Pilih pekerjaan", exact=True)
        if pekerjaan.count() > 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}=== field pekerjaan ditemukan{Colors.ENDC}")
            pekerjaan.click()
            pilihan_pekerjaan = page.get_by_text(format_cell_value(data["pekerjaan"]), exact=True)
            if pilihan_pekerjaan.count() > 0:
                print(f"pekerjaan di excel : {format_cell_value(data['pekerjaan'])}")
                pilihan_pekerjaan.click()

    # page.get_by_text("Pilih pekerjaan", exact=True).click()
    # page.get_by_text(format_cell_value(data["pekerjaan"]), exact=True).click()

    # page.pause()
    
    print("mencari field nama sekolah...")
    pilih_sekolah = page.get_by_text("Pilih nama sekolah", exact=True)
    if pilih_sekolah.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field nama sekolah ditemukan{Colors.ENDC}")
        pilih_sekolah.click()
    nama_sekolah_search = page.get_by_placeholder("Cari nama sekolah")
    if nama_sekolah_search.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== input nama sekolah ditemukan{Colors.ENDC}")
        print(f"nama sekolah di excel : {format_cell_value(data['sekolah'])}")
        nama_sekolah_search.click()
        nama_sekolah_search.press_sequentially(format_cell_value(data["sekolah"]), delay=100)
        page.wait_for_selector('[data-v-0dd0c770].flex.items-center.justify-between.gap-2')
    first_result = page.locator('[data-v-0dd0c770].flex.items-center.justify-between.gap-2').first
    if first_result.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== hasil nama sekolah ditemukan{Colors.ENDC}")
        first_result.click()

    print("mencari field jenjang pendidikan...")
    jenjang_pendidikan = page.get_by_text("Pilih jenjang pendidikan", exact=True)
    if jenjang_pendidikan.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field jenjang pendidikan ditemukan{Colors.ENDC}")
        jenjang_pendidikan.click()
    pilihan_jenjang = page.get_by_placeholder("Cari jenjang pendidikan")
    if pilihan_jenjang.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== input jenjang pendidikan ditemukan{Colors.ENDC}")
        print(f"jenjang pendidikan di excel : {format_cell_value(data['jenjang_pendidikan'])}")
        pilihan_jenjang.click()
        pilihan_jenjang.press_sequentially(format_cell_value(data["jenjang_pendidikan"]), delay=100)
        page.wait_for_selector('[data-v-0dd0c770].flex.items-center.justify-between.gap-2')
    first_result = page.locator('[data-v-0dd0c770].flex.items-center.justify-between.gap-2').first
    if first_result.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== hasil jenjang pendidikan ditemukan{Colors.ENDC}")
        first_result.click()

    print("mencari field alamat domisili...")
    alamat_domisili = page.get_by_text("Pilih alamat domisili", exact=True)
    if alamat_domisili.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== field alamat domisili ditemukan{Colors.ENDC}")
        alamat_domisili.click()

    for label, key in (("provinsi", "prov"), ("kabupaten", "kab"), ("kecamatan", "kec"), ("desa", "desa")):
        print(f"mencari field {label}...")
        pilihan = page.get_by_text(format_cell_value(data[key]), exact=True)
        if pilihan.count() > 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}=== field {label} ditemukan{Colors.ENDC}")
            print(f"{label} di excel : {format_cell_value(data[key])}")
            pilihan.click()

    print("mencari detail domisili...")
    detail_domisili = page.locator("textarea#detail-domisili")
    if detail_domisili.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== detail domisili ditemukan{Colors.ENDC}")
        print(f"detail domisili di excel : {format_cell_value(data['domisili'])}")
        detail_domisili.fill(format_cell_value(data["domisili"]))

    print("mencari tombol selanjutnya...")
    selanjutnya = page.get_by_role("button", name="Selanjutnya")
    if selanjutnya.count() > 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol selanjutnya ditemukan{Colors.ENDC}")
        selanjutnya.click()
    print(f"{Colors.OKCYAN}Mohon tunggu sedang menunggu respon dari server CKG secara lengkap...{Colors.ENDC}")
    # page.pause()
    page.wait_for_timeout(1500)
    # page.get_by_role("button", name="Tutup").click()
    # Seharusnya menunggu apakah tombol pilih muncul
    # jika tombol pilih muncul maka klik tombol pilih
    # jika tombol pilih di-klik maka klik Daftarkan dengan NIK
    # jika Daftarkan dengan NIK diklik, maka tunggu respon
    # jika ada tombol Ok, maka Raise Exception
    # jika tidak muncul maka klik Daftarkan tanpa NIK

    # locators = {
    #     "dengan_nik": page.get_by_role("button", name="Pilih"),
    #     "tanpa_nik": page.get_by_role("button", name="Daftarkan tanpa NIK")
    # }
    # nik_found = wait_for_first_visible(page, locators)
    # print(f"nik_found = {nik_found}")
    # if(nik_found == "dengan_nik"):
    #     locators["dengan_nik"].click()
    #     print(f"{Colors.OKCYAN}NIK ditemukan, silahkan tunggu...{Colors.ENDC}")
    #     page.get_by_role("button", name="Daftarkan dengan NIK").click()


    # elif(nik_found == "tanpa_nik"):
    #     locators["tanpa_nik"].click()

    # page.wait_for_load_state("networkidle")

    locators = {
        "exception": page.get_by_role("button", name="Ok", exact=True),
        "tutup": page.get_by_role("button", name="Tutup")
    }
    exception_found = wait_for_first_visible(page, locators)
    if (exception_found == "exception"):
        print("mencari tombol OK...")
        if locators["exception"].count() > 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol OK ditemukan{Colors.ENDC}")
            locators["exception"].click()
        raise SkipRowException("Ada error dari Server CKG - Biasanya terkait NIK yang tidak valid")
    else:
        print("mencari tombol tutup...")
        if locators["tutup"].count() > 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}=== tombol tutup ditemukan{Colors.ENDC}")
            locators["tutup"].click()
            print(f"{Colors.OKGREEN}{Colors.BOLD}============ Pendaftaran Berhasil ==========={Colors.ENDC}")


def main() -> dict:
    excel_path, sheet_name = resolve_dataset("pendaftaran_sekolah")
    username = get_required_env(USERNAME_ENV)
    password = get_required_env(PASSWORD_ENV)
    excel = ExcelStatusWorkbook(excel_path, sheet_name=sheet_name)
    data_rows = excel.pending_rows()
    if not data_rows:
        print(f"{Colors.WARNING}Tidak ada data pada file Excel.{Colors.ENDC}")
        return {"status": "success"}

    any_failed = False

    with sync_playwright() as p:
        browser, _window_layout = launch_chromium_with_layout(p)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        login_and_wait_for_profile(page, username, password)

        failed_rows = []
        date_picker = DatePicker()

        for row_entry in data_rows:
            index = row_entry["row_number"]
            data = row_entry["data"]
            try:
                register_single_entry(page, data, index, date_picker)
                excel.update_status(index, "SUCCESS")
                excel.append_row_to_dataset("konfirm_kehadiran_sekolah", {
                    "nama_lengkap": format_cell_value(data["nama_lengkap"]),
                    "tgl_entri": datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d"),
                })
            except SkipRowException as exc:
                # excel.update_status(index, f"SKIPPED: {str(exc)}")
                excel.update_status(index, str(exc))
            except Exception as exc:
                failed_rows.append(index)
                any_failed = True
                excel.update_status(index, f"FAILED: {exc}")
                # print(f"Baris Excel {index} gagal diproses: {exc}")
        print(f"{Colors.OKCYAN}Pendaftaran selesai, silahkan buka kembali file Excel Anda. Jika ditemukan DUKCAPIL NOTICE maka jalankan kembali agar diproses ulang.{Colors.ENDC}")
        context.close()
        browser.close()

    if any_failed:
        return {"status": "failed", "error_message": f"{len(failed_rows)} baris gagal diproses"}
    return {"status": "success"}

if __name__ == "__main__":
    username = os.getenv("CKG_USERNAME", "unknown")
    monitored_main(f"pendaftaran - {username}", main)
