import os
import queue
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from ckg_helper import (
    APP_NAME,
    MENU_ITEMS,
    PASSWORD_ENV,
    USERNAME_ENV,
    get_app_root,
    load_app_env,
    read_env_file,
    write_env_file,
    chromium_is_installed,
    run_playwright_cli,
)
from src.helpers.auto_update import (
    __version__,
    check_for_update,
    install_update,
)
from src.helpers.excel import (
    DEFAULT_COMBINED_WORKBOOK_NAME,
    find_matching_sheet,
    resolve_dataset,
)
from src.helpers.wali_config import (
    WALI_ENV_KEYS,
    get_wali_config,
    is_wali_config_complete,
    save_wali_config_to_env,
)
from datetime import datetime, timedelta

from src.epuskesmas.laporan_bpjs import (
    EPUSKESMAS_URL_ENV,
    EPUSKESMAS_USERNAME_ENV,
    EPUSKESMAS_PASSWORD_ENV,
    validate_date_range,
)
from PIL import Image, ImageTk

from src.gui.components import CTkDatePicker
from src.gui.runner import TaskExecutionWorker

import ui_theme as ui
from ui_theme import C, font


ctk.set_default_color_theme("blue")

# (category key used by the logic, title shown in header/sidebar, icon file in ./icons)
PAGES = [
    ("CKG Umum", "CKG Umum", "clipboard-list"),
    ("CKG Sekolah", "CKG Sekolah", "school"),
    ("ePuskesmas", "ePuskesmas", "hospital"),
    ("Pengaturan", "Pengaturan Akun", "settings"),
    ("Support", "Support & Donasi", "heart"),
]
PAGE_TITLES = {key: title for key, title, _ in PAGES}
WALI_GENDER_OPTIONS = ("Laki-laki", "Perempuan")
WALI_GENDER_PLACEHOLDER = "Pilih Jenis Kelamin"
SCHOOL_PREPARATION_DETAIL = "Persiapan Data CKG Sekolah"


class CKGHelperApp(ctk.CTk):
    def __init__(self, auto_check_update: bool = True):
        # Appearance must be set before the window exists. Default: follow the OS.
        root_dir = get_app_root()
        self._appearance_mode = ui.load_appearance(root_dir)
        ui.init_appearance(self._appearance_mode)

        super().__init__()

        self.app_root = root_dir
        load_app_env(self.app_root)

        self.title("CKG Helper - Otomasi Cek Kesehatan Gratis")
        self.geometry("980x700")
        self.minsize(860, 580)

        self.log_queue = queue.Queue()
        self.callback_queue = queue.Queue()
        self.worker: TaskExecutionWorker | None = None
        self.active_category = "CKG Umum"
        self.current_selected_task: dict | None = None

        # Set Window Icon dari icon.png
        self._load_window_icon()

        # Grid config
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

        # Cmd+, (Settings) on macOS, Cmd/Ctrl+1..5 to switch pages
        ui.setup_window(
            self,
            on_preferences=lambda: self._select_category("Pengaturan"),
            page_shortcuts=[lambda k=key: self._select_category(k) for key, _, _ in PAGES],
        )

        self.update_info: dict | None = None
        self.is_checking_update: bool = False
        self._poll_job = None
        self._update_job = None

        # Mulai antrian pembacaan log
        self._poll_log_queue()

        # Set default category
        self._select_category("CKG Umum")

        # Cek pembaruan aplikasi di latar belakang
        if auto_check_update:
            self._update_job = self.after(500, self._check_update_async)

    def _load_window_icon(self):
        icon_path = self.app_root / "icon.png"
        if icon_path.exists():
            try:
                pil_icon = Image.open(icon_path)
                self._app_icon = ImageTk.PhotoImage(pil_icon)
                self.iconphoto(False, self._app_icon)
            except Exception:
                pass

    # -------------------------------------------------------------
    # Small UI helpers
    # -------------------------------------------------------------
    def _set_status(self, text: str, kind: str = "ok"):
        """kind: ok (green) | warn (amber) | danger (red) | muted"""
        ui.set_status(self.lbl_status, text, kind)

    def _ui_idle(self):
        ui.style_button(self.btn_run, "primary", "play")
        self.btn_run.configure(state="normal")
        ui.style_button(self.btn_stop, "secondary", "square")
        self.btn_stop.configure(state="disabled")

    def _ui_running(self):
        ui.style_button(self.btn_run, "secondary", "play")
        self.btn_run.configure(state="disabled")
        ui.style_button(self.btn_stop, "danger", "square")
        self.btn_stop.configure(state="normal")

    def _set_update_status(self, text: str, kind: str = "info"):
        icon_name, color_kind = {
            "info": ("refresh-cw", "muted"),
            "ok": ("circle-check", "ok"),
            "new": ("download", "accent"),
        }[kind]
        ui.set_status(self.lbl_update_status, text, color_kind, icon_name)

    def _section_card(self, parent, title: str, subtitle: str | None = None):
        """Card with a title (and optional muted subtitle). Returns (card, body)."""
        c = ui.card(parent)
        c.pack(fill="x", padx=2, pady=(0, 14))
        ui.section_title(c, title).pack(anchor="w", padx=20, pady=(16, 2))
        if subtitle:
            ui.muted_label(c, subtitle, wrap_in=c).pack(anchor="w", padx=20, pady=(0, 4))
        body = ctk.CTkFrame(c, fg_color="transparent")
        body.pack(fill="x", padx=20, pady=(8, 18))
        body.grid_columnconfigure(0, minsize=170)
        body.grid_columnconfigure(1, weight=1)
        return c, body

    def _labeled_entry(self, body, row: int, label: str, value: str = "",
                       show: str | None = None, placeholder: str | None = None):
        ui.field_label(body, label).grid(row=row, column=0, sticky="w", pady=5, padx=(0, 14))
        kwargs = {}
        if show:
            kwargs["show"] = show
        if placeholder:
            kwargs["placeholder_text"] = placeholder
        ent = ui.entry(body, **kwargs)
        ent.insert(0, value)
        ent.grid(row=row, column=1, sticky="ew", pady=5)
        return ent

    # -------------------------------------------------------------
    # Sidebar
    # -------------------------------------------------------------
    def _make_nav_button(self, key: str, title: str, icon_name: str):
        return ui.NavButton(
            self.sidebar_frame, title, icon_name,
            command=lambda k=key: self._select_category(k),
        )

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=C.SIDEBAR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.pack_propagate(False)

        # Title & Icon Logo
        header_sidebar = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        header_sidebar.pack(fill="x", padx=16, pady=(20, 0))

        icon_path = self.app_root / "icon.png"
        if icon_path.exists():
            try:
                pil_img = Image.open(icon_path)
                self.logo_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(32, 32))
                self.logo_icon_label = ctk.CTkLabel(header_sidebar, text="", image=self.logo_image)
                self.logo_icon_label.pack(side="left", padx=(0, 8))
            except Exception:
                pass

        self.logo_label = ctk.CTkLabel(
            header_sidebar,
            text="CKG Helper",
            font=font(19, "bold"),
            text_color=C.TEXT,
        )
        self.logo_label.pack(side="left")

        self.version_badge = ctk.CTkLabel(
            self.sidebar_frame,
            text=f"v{__version__}",
            font=font(12),
            text_color=C.TEXT_MUTED,
            anchor="w",
        )
        self.version_badge.pack(fill="x", padx=18, pady=(2, 16))

        # Functional pages on top
        self.nav_buttons = {}
        for key, title, icon_name in PAGES:
            if key == "Support":
                continue
            btn = self._make_nav_button(key, title, icon_name)
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        # Bottom group, packed bottom-up: theme switcher, label, divider, Support
        self.theme_switcher = ui.ThemeSwitcher(
            self.sidebar_frame,
            current=self._appearance_mode,
            save_cb=self._change_appearance_mode,
        )
        self.theme_switcher.pack(side="bottom", fill="x", padx=12, pady=(0, 16))

        self.theme_label = ctk.CTkLabel(
            self.sidebar_frame, text="Tema", font=font(12), text_color=C.TEXT_MUTED, anchor="w"
        )
        self.theme_label.pack(side="bottom", fill="x", padx=18, pady=(0, 4))

        ctk.CTkFrame(self.sidebar_frame, height=1, fg_color=C.BORDER).pack(
            side="bottom", fill="x", padx=14, pady=(8, 12)
        )

        support_btn = self._make_nav_button("Support", PAGE_TITLES["Support"], "heart")
        support_btn.pack(side="bottom", fill="x", padx=10, pady=2)
        self.nav_buttons["Support"] = support_btn

        # Backward-compatible names used elsewhere in the code
        self.btn_umum = self.nav_buttons["CKG Umum"]
        self.btn_sekolah = self.nav_buttons["CKG Sekolah"]
        self.btn_epuskesmas = self.nav_buttons["ePuskesmas"]
        self.btn_settings = self.nav_buttons["Pengaturan"]
        self.btn_support = self.nav_buttons["Support"]

    # -------------------------------------------------------------
    # Main Content Area
    # -------------------------------------------------------------
    def _build_main_area(self):
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=24, pady=22)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(2, weight=1)

        # Header Title
        self.header_title = ui.title_label(self.main_container, "CKG Umum")
        self.header_title.grid(row=0, column=0, sticky="w", pady=(0, 14))

        # View Frame for Task or Settings
        self.task_view_frame = ui.card(self.main_container)
        self.task_view_frame.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        self.task_view_frame.grid_columnconfigure(0, minsize=150)
        self.task_view_frame.grid_columnconfigure(1, weight=1)

        self._build_task_controls()

        # Settings Frame (hidden by default)
        self.settings_frame = ui.scroll_area(self.main_container)
        self._build_settings_controls()

        # Support Frame (hidden by default)
        self.support_frame = ui.scroll_area(self.main_container)
        self._build_support_controls()

        # Log Console Area
        self._build_log_console()

    def _build_task_controls(self):
        # 1. Pilihan Sub-Tugas
        ui.field_label(self.task_view_frame, "Pilih Layanan:").grid(
            row=0, column=0, padx=(20, 0), pady=(18, 6), sticky="w"
        )

        self.task_option_menu = ui.option_menu(
            self.task_view_frame,
            values=["Pendaftaran Baru"],
            command=self._on_task_selected,
            width=320,
        )
        self.task_option_menu.grid(row=0, column=1, padx=(0, 20), pady=(18, 6), sticky="w")

        # 2. Form Periode Tanggal (Khusus ePuskesmas)
        today_str = datetime.today().strftime("%d-%m-%Y")
        self.epuskesmas_date_frame = ctk.CTkFrame(self.task_view_frame, fg_color="transparent")
        self.epuskesmas_date_frame.grid_columnconfigure(0, minsize=130)
        self.epuskesmas_date_frame.grid_columnconfigure(1, weight=1)

        ui.field_label(self.epuskesmas_date_frame, "Periode Laporan:").grid(
            row=0, column=0, pady=4, sticky="w"
        )

        date_inputs = ctk.CTkFrame(self.epuskesmas_date_frame, fg_color="transparent")
        date_inputs.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(date_inputs, text="Dari:", font=font(13), text_color=C.TEXT).grid(
            row=0, column=0, padx=(0, 6)
        )
        self.picker_tgl_awal = CTkDatePicker(date_inputs, fg_color="transparent")
        self.picker_tgl_awal.set_date_format("%d-%m-%Y")
        self.picker_tgl_awal.set_date(today_str)
        self.picker_tgl_awal.grid(row=0, column=1, padx=(0, 12))

        ctk.CTkLabel(date_inputs, text="s/d:", font=font(13), text_color=C.TEXT).grid(
            row=0, column=2, padx=(0, 6)
        )
        self.picker_tgl_akhir = CTkDatePicker(date_inputs, fg_color="transparent")
        self.picker_tgl_akhir.set_date_format("%d-%m-%Y")
        self.picker_tgl_akhir.set_date(today_str)
        self.picker_tgl_akhir.grid(row=0, column=3, padx=(0, 16))

        # Quick-pick buttons get their own row so the date row never overflows
        # at the minimum window width.
        quick_row = ctk.CTkFrame(self.epuskesmas_date_frame, fg_color="transparent")
        quick_row.grid(row=1, column=1, sticky="w", pady=(8, 0))

        btn_today = ui.secondary_button(
            quick_row, "Hari Ini", self._set_date_today, height=28, size=12
        )
        btn_today.pack(side="left", padx=(0, 6))

        btn_yesterday = ui.secondary_button(
            quick_row, "H-1 s/d Hari Ini", self._set_date_yesterday, height=28, size=12
        )
        btn_yesterday.pack(side="left")

        lbl_date_hint = ui.muted_label(
            self.epuskesmas_date_frame,
            "Format: DD-MM-YYYY (contoh: 13-10-2026). Rentang maksimal 3 hari.",
            size=12,
        )
        lbl_date_hint.grid(row=2, column=1, sticky="w", pady=(6, 4))

        self.school_prep_options_frame = ctk.CTkFrame(
            self.task_view_frame, fg_color="transparent"
        )
        self.school_prep_options_frame.grid_columnconfigure(0, minsize=130)
        ui.field_label(self.school_prep_options_frame, "Opsi Scraping:").grid(
            row=0, column=0, pady=4, sticky="w"
        )
        self.chk_repeat_all = ui.checkbox(
            self.school_prep_options_frame, "Ulang Semua"
        )
        self.chk_repeat_all.grid(row=0, column=1, sticky="w")
        self.school_prep_options_frame.grid_remove()

        # 3. File Excel Dataset
        ui.field_label(self.task_view_frame, "File Dataset:").grid(
            row=2, column=0, padx=(20, 0), pady=6, sticky="w"
        )

        dataset_row = ctk.CTkFrame(self.task_view_frame, fg_color="transparent")
        dataset_row.grid(row=2, column=1, padx=(0, 20), pady=6, sticky="ew")
        dataset_row.grid_columnconfigure(0, weight=1)

        default_dataset = str(self.app_root / "dataset" / DEFAULT_COMBINED_WORKBOOK_NAME)
        self.dataset_entry = ui.entry(dataset_row, placeholder_text=default_dataset)
        self.dataset_entry.insert(0, default_dataset)
        self.dataset_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        btn_browse = ui.secondary_button(
            dataset_row, "Pilih File...", self._browse_excel_file, "file-spreadsheet"
        )
        btn_browse.grid(row=0, column=1, padx=(0, 8))

        btn_open_folder = ui.secondary_button(
            dataset_row, "Buka Folder", self._open_dataset_folder, "folder-open"
        )
        btn_open_folder.grid(row=0, column=2)

        # 4. Keterangan Sheet
        self.lbl_sheet_info = ui.muted_label(
            self.task_view_frame, "Sheet yang dibutuhkan: pendaftaran_umum", size=12
        )
        self.lbl_sheet_info.grid(row=3, column=1, padx=(0, 20), pady=(0, 8), sticky="w")

        # 5. Action Row (Checkbox + Run Button + Stop Button + Status)
        action_frame = ctk.CTkFrame(self.task_view_frame, fg_color="transparent")
        action_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=(8, 18), sticky="ew")
        action_frame.grid_columnconfigure(3, weight=1)

        self.chk_excel_closed = ui.checkbox(action_frame, "File Excel sudah disimpan dan ditutup")
        self.chk_excel_closed.select()
        self.chk_excel_closed.grid(row=0, column=0, sticky="w", padx=(0, 18))

        self.btn_run = ui.primary_button(
            action_frame, "Mulai Proses", self._start_task_execution, "play", height=38, size=14
        )
        self.btn_run.grid(row=0, column=1, padx=(0, 8))

        self.btn_stop = ui.secondary_button(
            action_frame, "Hentikan", self._stop_task_execution, "square", height=38, size=14
        )
        self.btn_stop.configure(state="disabled")
        self.btn_stop.grid(row=0, column=2, padx=(0, 18))

        self.lbl_status = ui.status_label(action_frame, "Status: Siap", "ok")
        self.lbl_status.configure(font=font(13, "bold"))
        self.lbl_status.grid(row=0, column=3, sticky="w")

    def _stop_task_execution(self):
        if self.worker and self.worker.is_running:
            self._set_status("Status: Dihentikan", "warn")
            self._ui_idle()
            self.worker.stop()

    @property
    def ent_tgl_awal(self):
        return self.picker_tgl_awal.date_entry

    @property
    def ent_tgl_akhir(self):
        return self.picker_tgl_akhir.date_entry

    def _set_date_today(self):
        t = datetime.today().strftime("%d-%m-%Y")
        self.picker_tgl_awal.set_date(t)
        self.picker_tgl_akhir.set_date(t)

    def _set_date_yesterday(self):
        t = datetime.today().strftime("%d-%m-%Y")
        y = (datetime.today() - timedelta(days=1)).strftime("%d-%m-%Y")
        self.picker_tgl_awal.set_date(y)
        self.picker_tgl_akhir.set_date(t)

    def _build_settings_controls(self):
        # Akun CKG
        _, f_acc = self._section_card(self.settings_frame, "Kredensial Akun CKG")
        self.ent_username = self._labeled_entry(
            f_acc, 0, "Username / Email:", os.getenv(USERNAME_ENV, "")
        )
        self.ent_password = self._labeled_entry(
            f_acc, 1, "Password CKG:", os.getenv(PASSWORD_ENV, ""), show="•"
        )
        ui.primary_button(f_acc, "Simpan Kredensial CKG", self._save_credentials).grid(
            row=2, column=1, sticky="w", pady=(12, 0)
        )

        # Data Wali
        _, f_wali = self._section_card(
            self.settings_frame,
            "Data Wali Fallback",
            "Dipakai untuk pendaftaran anak/remaja.",
        )
        wali_cfg = get_wali_config()
        self.wali_entries = {}
        for i, (key, label) in enumerate(WALI_ENV_KEYS.items()):
            if key == "WALI_TGL_LAHIR":
                ui.field_label(f_wali, f"{label}:").grid(
                    row=i, column=0, sticky="w", pady=5, padx=(0, 14)
                )
                picker = CTkDatePicker(f_wali, fg_color="transparent")
                picker.set_date_format("%Y-%m-%d")
                picker.set_date(wali_cfg.get(key, ""))
                picker.set_allow_manual_input(False)
                picker.grid(row=i, column=1, sticky="w", pady=5)
                self.wali_entries[key] = picker
            elif key == "WALI_GENDER":
                ui.field_label(f_wali, f"{label}:").grid(
                    row=i, column=0, sticky="w", pady=5, padx=(0, 14)
                )
                gender_menu = ui.option_menu(
                    f_wali,
                    values=[WALI_GENDER_PLACEHOLDER, *WALI_GENDER_OPTIONS],
                    width=320,
                )
                gender_menu.set(wali_cfg.get(key) if wali_cfg.get(key) in WALI_GENDER_OPTIONS else WALI_GENDER_PLACEHOLDER)
                gender_menu.grid(row=i, column=1, sticky="w", pady=5)
                self.wali_entries[key] = gender_menu
            else:
                self.wali_entries[key] = self._labeled_entry(f_wali, i, f"{label}:", wali_cfg.get(key, ""))
        ui.primary_button(f_wali, "Simpan Data Wali", self._save_wali_config).grid(
            row=len(WALI_ENV_KEYS), column=1, sticky="w", pady=(12, 0)
        )

        # Kredensial ePuskesmas
        _, f_epus = self._section_card(self.settings_frame, "Kredensial Akun ePuskesmas")
        self.ent_epus_url = self._labeled_entry(
            f_epus, 0, "URL ePuskesmas:", os.getenv(EPUSKESMAS_URL_ENV, ""),
            placeholder="https://situbondo.epuskesmas.id",
        )
        self.ent_epus_username = self._labeled_entry(
            f_epus, 1, "Username:", os.getenv(EPUSKESMAS_USERNAME_ENV, "")
        )
        self.ent_epus_password = self._labeled_entry(
            f_epus, 2, "Password:", os.getenv(EPUSKESMAS_PASSWORD_ENV, ""), show="•"
        )
        ui.primary_button(f_epus, "Simpan Kredensial ePuskesmas", self._save_epuskesmas_credentials).grid(
            row=3, column=1, sticky="w", pady=(12, 0)
        )

        # Chromium Browser Check
        _, f_browser = self._section_card(
            self.settings_frame, "Browser Chromium", "Browser yang digunakan untuk menjalankan otomasi."
        )
        ui.secondary_button(
            f_browser, "Periksa & Pasang Browser Chromium", self._check_and_install_chromium, "download"
        ).grid(row=0, column=0, columnspan=2, sticky="w")

    def _build_support_controls(self):
        # 1. Card Pembaruan Aplikasi
        card_update = ui.card(self.support_frame)
        card_update.pack(fill="x", padx=2, pady=(0, 14))
        card_update.grid_columnconfigure(0, weight=1)

        header_update = ctk.CTkFrame(card_update, fg_color="transparent")
        header_update.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 6))
        header_update.grid_columnconfigure(0, weight=1)

        ui.section_title(header_update, "Pembaruan Aplikasi").grid(row=0, column=0, sticky="w")

        self.btn_check_update = ui.secondary_button(
            header_update, "Periksa Pembaruan", lambda: self._check_update_async(manual=True),
            "refresh-cw", height=30, size=12,
        )
        self.btn_check_update.grid(row=0, column=1, sticky="e")

        self.lbl_update_status = ui.status_label(card_update, "", "muted", "refresh-cw")
        self.lbl_update_status.configure(wraplength=560)
        ui.auto_wrap(self.lbl_update_status, card_update, padding=60)
        self.lbl_update_status.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))
        self._set_update_status(f"Versi saat ini: v{__version__} • Memeriksa status rilis...", "info")

        # Tombol aksi pembaruan (muncul jika update tersedia)
        self.frame_update_actions = ctk.CTkFrame(card_update, fg_color="transparent")
        self.frame_update_actions.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 12))
        self.frame_update_actions.grid_remove()

        self.btn_install_update = ui.primary_button(
            self.frame_update_actions, "Pasang Update Otomatis", self._apply_auto_update, "rocket"
        )
        self.btn_install_update.pack(side="left", padx=(0, 8))

        self.btn_manual_download = ui.secondary_button(
            self.frame_update_actions, "Unduh Manual di GitHub", self._open_manual_download, "external-link"
        )
        self.btn_manual_download.pack(side="left")

        # Catatan rilis / changelog (muncul jika ada)
        self.frame_changelog = ctk.CTkFrame(card_update, fg_color="transparent")
        self.frame_changelog.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 16))
        self.frame_changelog.grid_columnconfigure(0, weight=1)
        self.frame_changelog.grid_remove()

        ctk.CTkLabel(
            self.frame_changelog,
            text="Catatan Rilis (Changelog):",
            font=font(12, "bold"),
            text_color=C.TEXT,
        ).pack(anchor="w", pady=(0, 4))

        self.txt_changelog = ui.textbox(self.frame_changelog, height=100, wrap="word")
        self.txt_changelog.pack(fill="x")
        self.txt_changelog.configure(state="disabled")

        # 2. Card Saweria: satu aksi utama, salin tautan sekunder
        card_saweria = ui.card(self.support_frame)
        card_saweria.pack(fill="x", padx=2, pady=(0, 14))

        ui.section_title(card_saweria, "Dukung Pembuat Aplikasi").pack(anchor="w", padx=20, pady=(16, 4))
        desc_saweria = (
            "Dukung kami untuk terus mengembangkan aplikasi yang bermanfaat. "
            "Anda dapat melakukan request aplikasi lainnya jika dirasa memang memberikan manfaat "
            "bagi banyak orang lainnya."
        )
        ui.muted_label(card_saweria, desc_saweria, wrap_in=card_saweria).pack(anchor="w", padx=20)

        f_saweria_btn = ctk.CTkFrame(card_saweria, fg_color="transparent")
        f_saweria_btn.pack(anchor="w", padx=20, pady=(14, 18))

        btn_saweria = ui.primary_button(
            f_saweria_btn, "Buka Saweria (saweria.co/stywn93)", self._open_saweria, "coffee"
        )
        btn_saweria.pack(side="left", padx=(0, 8))

        btn_copy_saweria = ui.secondary_button(
            f_saweria_btn, "Salin Tautan", self._copy_saweria_link, "copy"
        )
        btn_copy_saweria.pack(side="left")

        # 3. Card Telegram: dua tombol sekunder agar tidak bersaing dengan Saweria
        card_tele = ui.card(self.support_frame)
        card_tele.pack(fill="x", padx=2, pady=(0, 14))

        ui.section_title(card_tele, "Kontak & Bantuan Otomasi").pack(anchor="w", padx=20, pady=(16, 4))
        desc_tele = (
            "Mengalami kendala teknis, punya ide/saran pengembangan fitur baru, "
            "atau membutuhkan konsultasi integrasi otomasi kesehatan lainnya? "
            "Silakan hubungi langsung pengembang melalui Telegram."
        )
        ui.muted_label(card_tele, desc_tele, wrap_in=card_tele).pack(anchor="w", padx=20)

        f_tele_btn = ctk.CTkFrame(card_tele, fg_color="transparent")
        f_tele_btn.pack(anchor="w", padx=20, pady=(14, 18))

        btn_tele = ui.secondary_button(
            f_tele_btn, "Hubungi via Telegram (@stywn93)", self._open_telegram, "send"
        )
        btn_tele.pack(side="left", padx=(0, 8))

        btn_copy_tele = ui.secondary_button(
            f_tele_btn, "Salin Username", self._copy_telegram_handle, "copy"
        )
        btn_copy_tele.pack(side="left")

        # 4. Tentang: teks biasa, bukan kartu (versi sudah tampil di sidebar)
        about_text = (
            "Aplikasi Otomasi Pendaftaran & Pelaporan Cek Kesehatan Gratis (CKG) serta Integrasi "
            "ePuskesmas BPJS. Dibuat untuk memudahkan tenaga kesehatan dan operator faskes dalam "
            "penginputan data."
        )
        ui.muted_label(self.support_frame, about_text, wrap_in=self.support_frame, padding=56, size=12).pack(
            anchor="w", padx=6, pady=(2, 10)
        )

    def _check_update_async(self, manual: bool = False):
        if self.is_checking_update:
            return
        self.is_checking_update = True
        self.btn_check_update.configure(state="disabled", text="Memeriksa...")
        self._set_update_status(
            f"Versi saat ini: v{__version__} • Sedang memeriksa pembaruan dari GitHub...", "info"
        )

        def worker():
            info = check_for_update()

            def update_ui():
                self.is_checking_update = False
                self.btn_check_update.configure(state="normal", text="Periksa Pembaruan")
                self.update_info = info
                if info:
                    self._set_update_status(
                        f"Versi baru tersedia: {info['version']} (versi Anda: v{__version__})", "new"
                    )
                    self.btn_support.set_badge(True)
                    self.frame_update_actions.grid()
                    if info.get("changelog"):
                        self.txt_changelog.configure(state="normal")
                        self.txt_changelog.delete("1.0", "end")
                        self.txt_changelog.insert("1.0", info["changelog"].strip())
                        self.txt_changelog.configure(state="disabled")
                        self.frame_changelog.grid()
                    else:
                        self.frame_changelog.grid_remove()

                    if manual:
                        messagebox.showinfo(
                            "Pembaruan Tersedia",
                            f"Versi baru {info['version']} telah tersedia!\n\n"
                            "Anda dapat memasang update otomatis atau mengunduh rilis secara manual.",
                        )
                else:
                    self._set_update_status(
                        f"Sudah menggunakan versi terbaru (v{__version__}).", "ok"
                    )
                    self.btn_support.set_badge(False)
                    self.frame_update_actions.grid_remove()
                    self.frame_changelog.grid_remove()
                    if manual:
                        messagebox.showinfo(
                            "Pembaruan Aplikasi",
                            f"Aplikasi CKG Helper v{__version__} sudah menggunakan versi terbaru.",
                        )

            self.callback_queue.put(update_ui)

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        return t

    def _open_manual_download(self):
        if self.update_info and self.update_info.get("download_url"):
            webbrowser.open(self.update_info["download_url"])
        else:
            webbrowser.open("https://github.com/stywn93/CKG-Helper/releases/latest")

    def _apply_auto_update(self):
        if not getattr(sys, "frozen", False):
            res = messagebox.askyesno(
                "Mode Pengembang / Source Code",
                "Aplikasi dijalankan dari source code (bukan build executable).\n"
                "Untuk memperbarui kode sumber, gunakan 'git pull' di terminal.\n\n"
                "Apakah Anda ingin membuka halaman rilis GitHub untuk mengunduh versi build manual?",
            )
            if res:
                self._open_manual_download()
            return

        if not self.update_info:
            messagebox.showinfo("Informasi", "Tidak ada file pembaruan yang siap dipasang.")
            return

        if messagebox.askyesno(
            "Konfirmasi Pembaruan",
            f"Unduh dan pasang pembaruan {self.update_info['version']} sekarang?\n\n"
            "Aplikasi akan menutup sementara dan otomatis dimulai ulang setelah pembaruan selesai.",
        ):
            try:
                install_update(self.app_root, self.update_info)
            except Exception as exc:
                messagebox.showerror("Gagal Memperbarui", f"Terjadi kesalahan saat update:\n{exc}")

    def _open_saweria(self):
        webbrowser.open("https://saweria.co/stywn93")

    def _copy_saweria_link(self):
        self.clipboard_clear()
        self.clipboard_append("https://saweria.co/stywn93")
        messagebox.showinfo("Berhasil", "Tautan Saweria disalin ke clipboard:\nhttps://saweria.co/stywn93")

    def _open_telegram(self):
        webbrowser.open("https://t.me/stywn93")

    def _copy_telegram_handle(self):
        self.clipboard_clear()
        self.clipboard_append("@stywn93")
        messagebox.showinfo("Berhasil", "Username Telegram disalin ke clipboard:\n@stywn93")

    def _build_log_console(self):
        self.console_container = ui.card(self.main_container)
        self.console_container.grid(row=2, column=0, sticky="nsew")
        self.console_container.grid_columnconfigure(0, weight=1)
        self.console_container.grid_rowconfigure(1, weight=1)

        # Header Console
        console_header = ctk.CTkFrame(self.console_container, fg_color="transparent")
        console_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 8))
        console_header.grid_columnconfigure(0, weight=1)

        lbl_console = ctk.CTkLabel(
            console_header,
            text="  Terminal Output / Live Log",
            image=ui.icon("terminal", 16),
            compound="left",
            font=font(13, "bold"),
            text_color=C.TEXT,
            anchor="w",
        )
        lbl_console.grid(row=0, column=0, sticky="w")

        btn_copy = ui.secondary_button(
            console_header, "Salin Log", self._copy_log, "copy", height=28, size=12
        )
        btn_copy.grid(row=0, column=1, padx=(0, 6))

        btn_clear = ui.secondary_button(
            console_header, "Bersihkan", self._clear_log, "trash-2", height=28, size=12
        )
        btn_clear.grid(row=0, column=2)

        # Textbox
        self.log_textbox = ui.textbox(self.console_container, mono=True, wrap="char")
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

    # -------------------------------------------------------------
    # Log & Callback Polling Handlers
    # -------------------------------------------------------------
    def _poll_callbacks(self):
        try:
            while True:
                cb = self.callback_queue.get_nowait()
                try:
                    cb()
                except Exception:
                    pass
        except queue.Empty:
            pass

    def _poll_log_queue(self):
        self._poll_callbacks()
        try:
            while True:
                line = self.log_queue.get_nowait()
                self.log_textbox.insert("end", line)
                self.log_textbox.see("end")
        except queue.Empty:
            pass
        self._poll_job = self.after(50, self._poll_log_queue)

    def _clear_log(self):
        self.log_textbox.delete("1.0", "end")

    def _copy_log(self):
        text = self.log_textbox.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Berhasil", "Log telah disalin ke clipboard.")

    def destroy(self):
        if hasattr(self, "_update_job") and self._update_job:
            try:
                self.after_cancel(self._update_job)
            except Exception:
                pass
        if hasattr(self, "_poll_job") and self._poll_job:
            try:
                self.after_cancel(self._poll_job)
            except Exception:
                pass
        super().destroy()

    # -------------------------------------------------------------
    # Navigation & Category Switching
    # -------------------------------------------------------------
    def _select_category(self, category: str):
        self.active_category = category
        self.header_title.configure(text=PAGE_TITLES.get(category, category))

        # Style active sidebar button
        for name, btn in self.nav_buttons.items():
            btn.set_active(name == category)

        if category == "Pengaturan":
            self.task_view_frame.grid_remove()
            self.console_container.grid_remove()
            self.support_frame.grid_remove()
            self.main_container.grid_rowconfigure(1, weight=1)
            self.main_container.grid_rowconfigure(2, weight=0)
            self.settings_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        elif category == "Support":
            self.task_view_frame.grid_remove()
            self.console_container.grid_remove()
            self.settings_frame.grid_remove()
            self.main_container.grid_rowconfigure(1, weight=1)
            self.main_container.grid_rowconfigure(2, weight=0)
            self.support_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        else:
            self.settings_frame.grid_remove()
            self.support_frame.grid_remove()
            self.main_container.grid_rowconfigure(1, weight=0)
            self.main_container.grid_rowconfigure(2, weight=1)
            self.task_view_frame.grid(row=1, column=0, sticky="ew", pady=(0, 14))
            self.console_container.grid(row=2, column=0, sticky="nsew")
            if category == "ePuskesmas":
                self.epuskesmas_date_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=4, sticky="ew")
            else:
                self.epuskesmas_date_frame.grid_remove()
            self.school_prep_options_frame.grid_remove()
            self._update_task_options_for_category(category)

    def _update_task_options_for_category(self, category: str):
        matching_tasks = [m for m in MENU_ITEMS if m["label"] == category]
        task_details = [m["detail"] for m in matching_tasks]

        if not task_details:
            self.task_option_menu.configure(values=["-"])
            self.task_option_menu.set("-")
            self.current_selected_task = None
            return

        self.task_option_menu.configure(values=task_details)
        self.task_option_menu.set(task_details[0])
        self._on_task_selected(task_details[0])

    def _on_task_selected(self, detail: str):
        for item in MENU_ITEMS:
            if item["label"] == self.active_category and item["detail"] == detail:
                self.current_selected_task = item
                self.lbl_sheet_info.configure(text=f"Sheet yang dibutuhkan: {item.get('sheet', '-')}")
                if detail == SCHOOL_PREPARATION_DETAIL:
                    self.school_prep_options_frame.grid(
                        row=1, column=0, columnspan=2, padx=20, pady=4, sticky="ew"
                    )
                else:
                    self.school_prep_options_frame.grid_remove()
                return

    # -------------------------------------------------------------
    # File & Folder Handlers
    # -------------------------------------------------------------
    def _browse_excel_file(self):
        filetypes = [("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        selected = filedialog.askopenfilename(
            title="Pilih File Dataset Excel",
            initialdir=str(self.app_root / "dataset"),
            filetypes=filetypes,
        )
        if selected:
            self.dataset_entry.delete(0, "end")
            self.dataset_entry.insert(0, selected)

    def _open_dataset_folder(self):
        dataset_dir = self.app_root / "dataset"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        if sys.platform == "darwin":
            subprocess.run(["open", str(dataset_dir)])
        elif sys.platform == "win32":
            subprocess.run(["explorer", str(dataset_dir)])
        else:
            subprocess.run(["xdg-open", str(dataset_dir)])

    # -------------------------------------------------------------
    # Settings Handlers
    # -------------------------------------------------------------
    def _save_credentials(self):
        user = self.ent_username.get().strip()
        pwd = self.ent_password.get().strip()
        if not user or not pwd:
            messagebox.showwarning("Peringatan", "Username dan password tidak boleh kosong.")
            return

        env_path = self.app_root / ".env"
        values = read_env_file(env_path)
        values[USERNAME_ENV] = user
        values[PASSWORD_ENV] = pwd
        write_env_file(env_path, values)
        os.environ[USERNAME_ENV] = user
        os.environ[PASSWORD_ENV] = pwd
        messagebox.showinfo("Sukses", "Kredensial akun CKG berhasil disimpan.")

    def _save_wali_config(self):
        cfg = {}
        for key in WALI_ENV_KEYS:
            widget = self.wali_entries[key]
            if key == "WALI_TGL_LAHIR":
                cfg[key] = widget.get_date().strip()
            else:
                cfg[key] = widget.get().strip()

        try:
            datetime.strptime(cfg["WALI_TGL_LAHIR"], "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning(
                "Peringatan Data Wali",
                "Tanggal lahir wali harus dipilih dari kalender.",
            )
            return

        if cfg["WALI_GENDER"] not in WALI_GENDER_OPTIONS:
            messagebox.showwarning(
                "Peringatan Data Wali",
                "Silakan pilih jenis kelamin wali.",
            )
            return

        env_path = self.app_root / ".env"
        save_wali_config_to_env(env_path, cfg)
        for k, v in cfg.items():
            os.environ[k] = v
        messagebox.showinfo("Sukses", "Data wali fallback berhasil disimpan.")

    def _save_epuskesmas_credentials(self):
        url = self.ent_epus_url.get().strip()
        user = self.ent_epus_username.get().strip()
        pwd = self.ent_epus_password.get().strip()
        if not url or not user or not pwd:
            messagebox.showwarning("Peringatan", "URL, username, dan password ePuskesmas tidak boleh kosong.")
            return

        env_path = self.app_root / ".env"
        lines = []
        if env_path.exists():
            lines = env_path.read_text(encoding="utf-8").splitlines()

        updated = set()
        new_lines = []
        for line in lines:
            matched = False
            for k, v in [
                (EPUSKESMAS_URL_ENV, url),
                (EPUSKESMAS_USERNAME_ENV, user),
                (EPUSKESMAS_PASSWORD_ENV, pwd),
            ]:
                if line.startswith(f"{k}="):
                    new_lines.append(f"{k}={v}")
                    updated.add(k)
                    matched = True
                    break
            if not matched:
                new_lines.append(line)

        missing = [
            (k, v)
            for k, v in [
                (EPUSKESMAS_URL_ENV, url),
                (EPUSKESMAS_USERNAME_ENV, user),
                (EPUSKESMAS_PASSWORD_ENV, pwd),
            ]
            if k not in updated
        ]

        if missing:
            if new_lines and new_lines[-1].strip() != "":
                new_lines.append("")
            new_lines.append("# Konfigurasi ePuskesmas")
            for k, v in missing:
                new_lines.append(f"{k}={v}")

        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        os.environ[EPUSKESMAS_URL_ENV] = url
        os.environ[EPUSKESMAS_USERNAME_ENV] = user
        os.environ[EPUSKESMAS_PASSWORD_ENV] = pwd
        messagebox.showinfo("Sukses", "Kredensial akun ePuskesmas berhasil disimpan.")

    def _check_and_install_chromium(self):
        if chromium_is_installed():
            messagebox.showinfo("Info Browser", "Browser Chromium sudah terpasang dan siap digunakan.")
            return

        if messagebox.askyesno(
            "Unduh Chromium",
            "Chromium belum terpasang. Apakah Anda ingin mengunduhnya sekarang? (Perlu koneksi internet)",
        ):
            self._set_status("Status: Mengunduh Chromium...", "warn")
            self.btn_run.configure(state="disabled")

            def do_install():
                code = run_playwright_cli(["install", "chromium"])
                if code == 0 and chromium_is_installed():
                    self.after(0, lambda: messagebox.showinfo("Sukses", "Chromium berhasil dipasang."))
                    self.after(0, lambda: self._set_status("Status: Siap", "ok"))
                else:
                    self.after(0, lambda: messagebox.showerror("Gagal", "Gagal mengunduh Chromium."))
                    self.after(0, lambda: self._set_status("Status: Error Browser", "danger"))
                self.after(0, lambda: self.btn_run.configure(state="normal"))

            threading.Thread(target=do_install, daemon=True).start()

    def _change_appearance_mode(self, mode: str):
        ctk.set_appearance_mode(mode)
        self._appearance_mode = mode
        ui.save_appearance(self.app_root, mode)

    # -------------------------------------------------------------
    # Task Execution Handler
    # -------------------------------------------------------------
    def _start_task_execution(self):
        if self.worker and self.worker.is_running:
            messagebox.showwarning("Peringatan", "Proses masih berjalan. Harap tunggu hingga selesai.")
            return

        if not self.chk_excel_closed.get():
            messagebox.showwarning(
                "Peringatan Excel",
                "Mohon centang konfirmasi bahwa file Excel sudah disimpan dan ditutup.",
            )
            return

        if not self.current_selected_task:
            messagebox.showwarning("Peringatan", "Pilih layanan yang akan dijalankan terlebih dahulu.")
            return

        # Validasi Kredensial & Filter Tanggal
        if self.active_category == "ePuskesmas":
            epus_url = os.getenv(EPUSKESMAS_URL_ENV, "").strip()
            epus_user = os.getenv(EPUSKESMAS_USERNAME_ENV, "").strip()
            epus_pwd = os.getenv(EPUSKESMAS_PASSWORD_ENV, "").strip()
            if not epus_url or not epus_user or not epus_pwd:
                if messagebox.askyesno(
                    "Kredensial ePuskesmas Belum Lengkap",
                    "Akun ePuskesmas belum dikonfigurasi. Buka tab Pengaturan sekarang?",
                ):
                    self._select_category("Pengaturan")
                return

            tgl_awal = self.picker_tgl_awal.get_date().strip()
            tgl_akhir = self.picker_tgl_akhir.get_date().strip()

            try:
                val_start, val_end = validate_date_range(tgl_awal, tgl_akhir)
            except ValueError as err:
                messagebox.showerror("Periode Tanggal Tidak Valid", str(err))
                return

            os.environ["EPUSKESMAS_START_DATE"] = val_start
            os.environ["EPUSKESMAS_END_DATE"] = val_end
        else:
            # Cek kredensial CKG
            user = os.getenv(USERNAME_ENV)
            pwd = os.getenv(PASSWORD_ENV)
            if not user or not pwd:
                if messagebox.askyesno(
                    "Kredensial Belum Diatur",
                    "Akun CKG belum disetting. Buka tab Pengaturan sekarang?",
                ):
                    self._select_category("Pengaturan")
                return

            # Cek wali jika pendaftaran baru
            if self.current_selected_task.get("detail") == "Pendaftaran Baru":
                if not is_wali_config_complete():
                    if messagebox.askyesno(
                        "Data Wali Belum Lengkap",
                        "Pendaftaran Baru membutuhkan data Wali Fallback. Buka tab Pengaturan sekarang?",
                    ):
                        self._select_category("Pengaturan")
                    return

            if self.current_selected_task.get("detail") == SCHOOL_PREPARATION_DETAIL:
                os.environ["CKG_REPEAT_ALL"] = "1" if self.chk_repeat_all.get() else "0"

        # Atur file excel kustom jika user memilih file tertentu
        chosen_excel = Path(self.dataset_entry.get().strip())
        if chosen_excel.exists():
            # Jika user memilih file excel di dalam folder dataset
            if chosen_excel.parent.resolve() == (self.app_root / "dataset").resolve():
                os.environ["CKG_COMBINED_DATASET"] = chosen_excel.name
            else:
                # File di luar, salin atau set env
                os.environ["CKG_COMBINED_DATASET"] = chosen_excel.name
                # Copy ke dataset jika belum ada
                dest = self.app_root / "dataset" / chosen_excel.name
                if not dest.exists():
                    import shutil
                    shutil.copy2(chosen_excel, dest)

        # Cek Chromium
        if not chromium_is_installed():
            self._check_and_install_chromium()
            return

        # Inisialisasi Worker
        self._ui_running()
        self._set_status("Status: Berjalan...", "warn")

        def on_started():
            pass

        def on_finished(success: bool, msg: str):
            def update_ui():
                self._ui_idle()
                if success:
                    self._set_status("Status: Selesai", "ok")
                else:
                    if "dihentikan" in msg.lower():
                        self._set_status("Status: Dihentikan", "warn")
                    else:
                        self._set_status("Status: Gagal", "danger")
            self.after(0, update_ui)

        self.worker = TaskExecutionWorker(
            app_root=self.app_root,
            option=self.current_selected_task,
            log_queue=self.log_queue,
            on_started=on_started,
            on_finished=on_finished,
        )
        self.worker.start()


def main():
    app = CKGHelperApp()
    app.mainloop()


if __name__ == "__main__":
    main()
