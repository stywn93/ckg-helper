import os
import re
import sys
from pathlib import Path


HELPERS_DIR = Path(__file__).resolve().parents[1] / "helpers"
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

CKU_DIR = Path(__file__).resolve().parent.parent / "ckg-umum"
if str(CKU_DIR) not in sys.path:
    sys.path.insert(0, str(CKU_DIR))

from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

import click_delay  # noqa: F401
from api_report import monitored_main
from excel import ExcelAppendWorkbook, resolve_dataset
from playwright_window_layout import launch_chromium_with_layout
from sticky_stop_footer import sticky_stop_footer


PROJECT_ROOT = Path(os.getenv("CKG_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
load_dotenv(PROJECT_ROOT / ".env")

USERNAME_ENV = "CKG_USERNAME"
PASSWORD_ENV = "CKG_PASSWORD"
LOGIN_SUCCESS_TIMEOUT_MS = int(os.getenv("CKG_LOGIN_SUCCESS_TIMEOUT_MS", "60000"))
SCHOOL_PAGE_URL = "https://sehatindonesiaku.kemkes.go.id/ckg-pelayanan-sekolah"
SCHOOL_OPTION_SELECTORS = (
    "[role='option']:visible",
    "div.py-2.px-4.cursor-pointer:visible",
    ".max-h-\\[250px\\] div.cursor-pointer:visible",
)
SCHOOL_SEARCH_SELECTORS = ("#sekolah", "input[placeholder='Cari nama sekolah']")
OUTPUT_HEADERS = ("sekolah", "kelas", "nama_lengkap")
PAGINATION_SELECTOR = "ul.vpagination:visible"
STATUS_SHEET_NAME = "hasil_scraping_data_sekolah"
STATUS_HEADERS = ("sekolah", "kelas", "keterangan")
REPEAT_ALL_ENV = "CKG_REPEAT_ALL"


class Colors:
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} belum diisi.")
    return value


def clean_text(value) -> str:
    return " ".join(str(value or "").split())


def normalize_key(value) -> str:
    return clean_text(value).casefold()


def is_repeat_all_enabled(value: str | None = None) -> bool:
    if value is None:
        value = os.getenv(REPEAT_ALL_ENV, "")
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def should_skip_combination(
    school: str,
    class_name: str,
    scraped_combinations: set[tuple[str, str]],
    repeat_all: bool,
) -> bool:
    if repeat_all:
        return False
    return (normalize_key(school), normalize_key(class_name)) in scraped_combinations


def extract_name_values(headers: list[str], rows: list[list[str]]) -> list[str]:
    """Return non-empty, unique names from table rows."""
    headers = [clean_text(header) for header in headers]
    name_index = 0
    if headers:
        for index, header in enumerate(headers):
            if normalize_key(header) == "nama" or normalize_key(header).startswith("nama "):
                name_index = index
                break

    names = []
    seen = set()
    for row in rows:
        if not row or name_index >= len(row):
            continue
        name = clean_text(row[name_index])
        if not name or normalize_key(name) in {"nama", "nama lengkap"}:
            continue
        key = normalize_key(name)
        if key not in seen:
            names.append(name)
            seen.add(key)
    return names


class ServiceExcelWriter:
    """Append school service results while skipping existing school/class/name keys."""

    HEADER_ALIASES = {
        "sekolah": ("sekolah",),
        "kelas": ("kelas",),
        "nama_lengkap": ("nama_lengkap", "nama lengkap", "nama"),
    }

    def __init__(self, path: Path, sheet_name: str | None):
        self.writer = ExcelAppendWorkbook(path, sheet_name=sheet_name)
        self.sheet = self.writer.sheet
        self.headers = [clean_text(cell.value) for cell in self.sheet[1]]
        self.header_names = self._resolve_headers()
        self.existing_keys = self._load_existing_keys()
        self.status_sheet = self._prepare_status_sheet()

    def _resolve_headers(self) -> dict[str, str]:
        normalized_headers = {normalize_key(header): header for header in self.headers if header}
        resolved = {}
        for canonical, aliases in self.HEADER_ALIASES.items():
            for alias in aliases:
                if normalize_key(alias) in normalized_headers:
                    resolved[canonical] = normalized_headers[normalize_key(alias)]
                    break
        missing = [header for header in OUTPUT_HEADERS if header not in resolved]
        if missing:
            raise RuntimeError(
                "Sheet pelayanan_sekolah belum memiliki kolom: " + ", ".join(missing)
            )
        return resolved

    def _key(self, school: str, class_name: str, name: str) -> tuple[str, str, str]:
        return normalize_key(school), normalize_key(class_name), normalize_key(name)

    def _load_existing_keys(self) -> set[tuple[str, str, str]]:
        positions = {header: self.headers.index(header) for header in self.header_names.values()}
        keys = set()
        for row in self.sheet.iter_rows(min_row=2, values_only=True):
            keys.add(
                self._key(
                    row[positions[self.header_names["sekolah"]]] if len(row) > positions[self.header_names["sekolah"]] else "",
                    row[positions[self.header_names["kelas"]]] if len(row) > positions[self.header_names["kelas"]] else "",
                    row[positions[self.header_names["nama_lengkap"]]] if len(row) > positions[self.header_names["nama_lengkap"]] else "",
                )
            )
        return {key for key in keys if all(key)}

    def _prepare_status_sheet(self):
        workbook = self.writer.workbook
        if STATUS_SHEET_NAME in workbook.sheetnames:
            sheet = workbook[STATUS_SHEET_NAME]
        else:
            sheet = workbook.create_sheet(title=STATUS_SHEET_NAME)

        headers = [clean_text(cell.value) for cell in sheet[1]]
        if not any(headers):
            for column, header in enumerate(STATUS_HEADERS, start=1):
                sheet.cell(row=1, column=column, value=header)
        elif headers[: len(STATUS_HEADERS)] != list(STATUS_HEADERS):
            raise RuntimeError(
                f"Sheet {STATUS_SHEET_NAME} harus memiliki kolom: "
                + ", ".join(STATUS_HEADERS)
            )

        workbook.save(str(self.writer.path))
        return sheet

    def update_scrape_status(
        self,
        school: str,
        class_name: str,
        scraped_count: int | None = None,
        error: str | None = None,
    ) -> None:
        school = clean_text(school)
        class_name = clean_text(class_name)
        if error:
            description = f"GAGAL: {clean_text(error)}"
        else:
            description = f"{scraped_count or 0} data berhasil di-scrape"

        for row_number in range(2, self.status_sheet.max_row + 1):
            existing_school = self.status_sheet.cell(row=row_number, column=1).value
            existing_class = self.status_sheet.cell(row=row_number, column=2).value
            if (
                normalize_key(existing_school) == normalize_key(school)
                and normalize_key(existing_class) == normalize_key(class_name)
            ):
                status_row = row_number
                break
        else:
            status_row = self.status_sheet.max_row + 1

        self.status_sheet.cell(row=status_row, column=1, value=school)
        self.status_sheet.cell(row=status_row, column=2, value=class_name)
        self.status_sheet.cell(row=status_row, column=3, value=description)
        self.writer.workbook.save(str(self.writer.path))

    def scraped_combinations(self) -> set[tuple[str, str]]:
        combinations = set()
        for row in self.status_sheet.iter_rows(min_row=2, values_only=True):
            school = normalize_key(row[0] if len(row) > 0 else "")
            class_name = normalize_key(row[1] if len(row) > 1 else "")
            if school and class_name:
                combinations.add((school, class_name))
        return combinations

    def append_names(self, school: str, class_name: str, names: list[str]) -> tuple[int, int]:
        added = 0
        skipped = 0
        for name in names:
            name = clean_text(name)
            if not name:
                continue
            key = self._key(school, class_name, name)
            if key in self.existing_keys:
                skipped += 1
                continue

            self.writer.append_row(
                {
                    self.header_names["sekolah"]: clean_text(school),
                    self.header_names["kelas"]: clean_text(class_name),
                    self.header_names["nama_lengkap"]: name,
                }
            )
            self.existing_keys.add(key)
            added += 1
        return added, skipped


def prepare_service_page(page) -> None:
    page.goto(SCHOOL_PAGE_URL)
    page.wait_for_load_state("networkidle")
    page.reload(wait_until="networkidle")

    checkbox = page.locator("input[name='verify']")
    if checkbox.count() > 0:
        checkbox.set_checked(True, force=True)
        consent_button = page.get_by_role("button", name="Setuju", exact=True)
        if consent_button.count() > 0:
            consent_button.click()
            page.wait_for_load_state("networkidle")


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


def click_school_selector(page) -> None:
    for label in ("Pilih sekolah", "Pilih nama sekolah"):
        selector = page.get_by_text(label, exact=True)
        if selector.count() > 0:
            selector.first.click()
            return
    raise RuntimeError("Field sekolah tidak ditemukan.")


def school_search_input(page):
    for selector in SCHOOL_SEARCH_SELECTORS:
        locator = page.locator(selector)
        if locator.count() > 0:
            return locator.first
    raise RuntimeError("Input pencarian sekolah tidak ditemukan.")


def visible_option_texts(page) -> list[str]:
    values = []
    seen = set()
    for selector in SCHOOL_OPTION_SELECTORS:
        options = page.locator(selector)
        for index in range(options.count()):
            text = clean_text(options.nth(index).inner_text())
            key = normalize_key(text)
            if text and not key.startswith(("pilih ", "cari ")) and key not in seen:
                values.append(text)
                seen.add(key)
    return values


def click_visible_option(page, expected_text: str) -> None:
    expected_key = normalize_key(expected_text)
    for selector in SCHOOL_OPTION_SELECTORS:
        options = page.locator(selector)
        for index in range(options.count()):
            option = options.nth(index)
            if normalize_key(option.inner_text()) == expected_key:
                option.click()
                return
    raise RuntimeError(f"Opsi '{expected_text}' tidak ditemukan.")


def collect_school_names(page) -> list[str]:
    click_school_selector(page)
    # shortcut: reads rendered dropdown options; use the site's API if the list is virtualized.
    names = visible_option_texts(page)
    if not names:
        raise RuntimeError("Tidak ada daftar sekolah yang ditemukan dari website.")
    page.keyboard.press("Escape")
    return names


def select_school(page, school: str) -> None:
    click_school_selector(page)
    search = school_search_input(page)
    search.fill("")
    search.press_sequentially(school, delay=100)
    try:
        page.locator("[role='option']:visible, div.py-2.px-4.cursor-pointer:visible").first.wait_for(
            state="visible", timeout=5000
        )
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(f"Opsi sekolah '{school}' tidak muncul.") from exc
    click_visible_option(page, school)


def visible_native_class_select(page):
    selects = page.locator("select:visible")
    for index in range(selects.count()):
        select = selects.nth(index)
        options = [clean_text(value) for value in select.locator("option").all_text_contents()]
        options = [value for value in options if value and not value.lower().startswith("pilih")]
        if options:
            return select, options
    return None, []


def click_class_selector(page) -> None:
    selector = page.get_by_text("Pilih kelas", exact=True)
    if selector.count() == 0:
        raise RuntimeError("Field kelas tidak ditemukan.")
    selector.first.click()


def collect_class_names(page) -> list[str]:
    native_select, native_options = visible_native_class_select(page)
    if native_select:
        return native_options

    click_class_selector(page)
    names = visible_option_texts(page)
    if not names:
        raise RuntimeError("Tidak ada daftar kelas untuk sekolah yang dipilih.")
    page.keyboard.press("Escape")
    return names


def select_class(page, class_name: str) -> None:
    native_select, _ = visible_native_class_select(page)
    if native_select:
        native_select.select_option(label=class_name)
        return

    click_class_selector(page)
    click_visible_option(page, class_name)


def click_search_button(page) -> None:
    button = page.get_by_role("button", name="Tampilkan Pencarian", exact=True)
    if button.count() == 0:
        raise RuntimeError("Button Tampilkan Pencarian tidak ditemukan.")
    button.first.click()
    page.wait_for_load_state("networkidle")


def is_disabled_pagination_item(class_name: str | None) -> bool:
    return "disabled" in (class_name or "").split()


def _find_next_page(page):
    pagination = page.locator(PAGINATION_SELECTOR)
    if pagination.count() == 0:
        return None, None

    items = pagination.first.locator("li.page-item")
    for index in range(items.count()):
        item = items.nth(index)
        link = item.locator("a.page-link")
        if link.count() > 0 and clean_text(link.first.inner_text()) == ">":
            return item, link.first
    return None, None


def _active_page_number(page) -> str:
    active_page = page.locator(
        f"{PAGINATION_SELECTOR} li.page-item.active a.page-link"
    )
    if active_page.count() == 0:
        return ""
    return clean_text(active_page.first.inner_text())


def _wait_for_next_page(page, previous_page: str) -> None:
    if previous_page:
        try:
            page.wait_for_function(
                """
                (expected) => {
                    const active = document.querySelector(
                        'ul.vpagination li.page-item.active a.page-link'
                    );
                    return active && active.textContent.trim() !== expected;
                }
                """,
                arg=previous_page,
                timeout=5000,
            )
            return
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(
                f"Pagination tidak berpindah dari halaman {previous_page}."
            ) from exc
    page.wait_for_load_state("networkidle")


def scrape_paginated_names(page) -> list[str]:
    names = []
    visited_pages = set()

    while True:
        current_page = _active_page_number(page)
        page_key = current_page or f"unknown-{len(visited_pages) + 1}"
        if page_key in visited_pages:
            raise RuntimeError(f"Pagination kembali ke halaman {page_key}.")
        visited_pages.add(page_key)

        names.extend(scrape_names(page))

        pagination_item, next_link = _find_next_page(page)
        if pagination_item is None:
            break
        if is_disabled_pagination_item(pagination_item.get_attribute("class")):
            break

        previous_page = current_page
        next_link.click()
        _wait_for_next_page(page, previous_page)

    return names


def _table_headers(table) -> list[str]:
    headers = table.locator("thead th:visible").all_text_contents()
    if headers:
        return headers
    first_row = table.locator("tr:visible").first
    return first_row.locator("th:visible").all_text_contents()


def scrape_names(page) -> list[str]:
    tables = page.locator("table:visible")
    for index in range(tables.count()):
        table = tables.nth(index)
        headers = _table_headers(table)
        rows = table.locator("tbody tr:visible")
        row_start = 0
        if rows.count() == 0:
            rows = table.locator("tr:visible")
            row_start = 1 if headers and rows.count() > 0 else 0

        row_values = []
        for row_index in range(row_start, rows.count()):
            cells = rows.nth(row_index).locator("td:visible").all_text_contents()
            if cells:
                row_values.append(cells)

        names = extract_name_values(headers, row_values)
        if names or row_values:
            return names
    raise RuntimeError("Tabel hasil pencarian tidak ditemukan.")


def process_school_class(
    page, school: str, class_name: str, excel: ServiceExcelWriter
) -> tuple[int, int, int]:
    prepare_service_page(page)
    select_school(page, school)
    select_class(page, class_name)
    click_search_button(page)
    names = scrape_paginated_names(page)
    added, skipped = excel.append_names(school, class_name, names)
    return added, skipped, len(names)


def _run_main() -> dict:
    excel_path, sheet_name = resolve_dataset("pelayanan_sekolah")
    if not excel_path.exists():
        raise RuntimeError(
            f"Dataset pelayanan sekolah tidak ditemukan: {excel_path}. "
            "Buat sheet pelayanan_sekolah dengan kolom sekolah, kelas, nama_lengkap."
        )

    username = get_required_env(USERNAME_ENV)
    password = get_required_env(PASSWORD_ENV)
    excel = ServiceExcelWriter(excel_path, sheet_name)
    repeat_all = is_repeat_all_enabled()
    scraped_combinations = set() if repeat_all else excel.scraped_combinations()
    any_failed = False
    failed_combinations = []

    if repeat_all:
        print(f"{Colors.OKCYAN}Mode: Ulang Semua aktif.{Colors.ENDC}")
    else:
        print(
            f"{Colors.OKCYAN}Mode: melanjutkan scraping. "
            f"{len(scraped_combinations)} kombinasi sekolah/kelas dilewati.{Colors.ENDC}"
        )

    with sync_playwright() as playwright:
        browser, _window_layout = launch_chromium_with_layout(playwright)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        try:
            login_and_wait_for_profile(page, username, password)
            prepare_service_page(page)
            schools = collect_school_names(page)
            print(f"{Colors.OKCYAN}Ditemukan {len(schools)} sekolah.{Colors.ENDC}")

            for school_index, school in enumerate(schools, start=1):
                try:
                    prepare_service_page(page)
                    select_school(page, school)
                    classes = collect_class_names(page)
                    print(
                        f"{Colors.OKCYAN}[{school_index}/{len(schools)}] {school}: "
                        f"{len(classes)} kelas.{Colors.ENDC}"
                    )
                except Exception as exc:
                    any_failed = True
                    failed_combinations.append(f"{school}: {exc}")
                    print(f"{Colors.FAIL}Gagal membaca sekolah {school}: {exc}{Colors.ENDC}")
                    continue

                for class_index, class_name in enumerate(classes, start=1):
                    if should_skip_combination(
                        school, class_name, scraped_combinations, repeat_all
                    ):
                        print(
                            f"{Colors.OKCYAN}  Kelas {class_index}/{len(classes)} "
                            f"{class_name}: dilewati, sudah ada di hasil scraping.{Colors.ENDC}"
                        )
                        continue

                    try:
                        added, skipped, scraped_count = process_school_class(
                            page, school, class_name, excel
                        )
                        excel.update_scrape_status(
                            school, class_name, scraped_count=scraped_count
                        )
                        scraped_combinations.add(
                            (normalize_key(school), normalize_key(class_name))
                        )
                        print(
                            f"{Colors.OKGREEN}  Kelas {class_index}/{len(classes)} "
                            f"{class_name}: {scraped_count} di-scrape, "
                            f"{added} ditambahkan, {skipped} duplikat dilewati.{Colors.ENDC}"
                        )
                    except Exception as exc:
                        any_failed = True
                        failed_combinations.append(f"{school} / {class_name}: {exc}")
                        excel.update_scrape_status(school, class_name, error=str(exc))
                        print(
                            f"{Colors.FAIL}  Gagal memproses {school} / {class_name}: "
                            f"{exc}{Colors.ENDC}"
                        )
        finally:
            context.close()
            browser.close()

    if any_failed:
        return {
            "status": "failed",
            "error_message": f"{len(failed_combinations)} kombinasi sekolah/kelas gagal diproses",
        }
    print(f"{Colors.OKGREEN}Scraping pelayanan CKG sekolah selesai.{Colors.ENDC}")
    return {"status": "success"}


def main() -> dict:
    with sticky_stop_footer():
        return _run_main()


if __name__ == "__main__":
    username = os.getenv(USERNAME_ENV, "unknown")
    monitored_main(f"pelayanan_sekolah - {username}", main)
