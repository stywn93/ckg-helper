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
from dotenv import load_dotenv

from ckg_helper import (
    APP_NAME,
    MENU_ITEMS,
    PASSWORD_ENV,
    USERNAME_ENV,
    get_app_root,
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



ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class CKGHelperApp(ctk.CTk):
    def __init__(self, auto_check_update: bool = True):
        super().__init__()

        self.app_root = get_app_root()
        load_dotenv(self.app_root / ".env")

        self.title(f"CKG Helper v{__version__} - Otomasi Cek Kesehatan Gratis")
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
    # Sidebar
    # -------------------------------------------------------------
    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        # Title & Icon Logo
        header_sidebar = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        header_sidebar.grid(row=0, column=0, padx=15, pady=(15, 2), sticky="w")

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
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.pack(side="left")

        self.version_badge = ctk.CTkLabel(
            self.sidebar_frame,
            text=f"v{__version__} • Desktop GUI",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.version_badge.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")


        # Category buttons
        self.btn_umum = ctk.CTkButton(
            self.sidebar_frame,
            text="📋  CKG Umum",
            anchor="w",
            command=lambda: self._select_category("CKG Umum"),
        )
        self.btn_umum.grid(row=2, column=0, padx=15, pady=6, sticky="ew")

        self.btn_sekolah = ctk.CTkButton(
            self.sidebar_frame,
            text="🏫  CKG Sekolah",
            anchor="w",
            command=lambda: self._select_category("CKG Sekolah"),
        )
        self.btn_sekolah.grid(row=3, column=0, padx=15, pady=6, sticky="ew")

        self.btn_epuskesmas = ctk.CTkButton(
            self.sidebar_frame,
            text="🏥  ePuskesmas",
            anchor="w",
            command=lambda: self._select_category("ePuskesmas"),
        )
        self.btn_epuskesmas.grid(row=4, column=0, padx=15, pady=6, sticky="ew")

        self.btn_settings = ctk.CTkButton(
            self.sidebar_frame,
            text="⚙️  Pengaturan Akun",
            anchor="w",
            command=lambda: self._select_category("Pengaturan"),
        )
        self.btn_settings.grid(row=5, column=0, padx=15, pady=6, sticky="ew")

        self.btn_support = ctk.CTkButton(
            self.sidebar_frame,
            text="💖  Support",
            anchor="w",
            command=lambda: self._select_category("Support"),
        )
        self.btn_support.grid(row=6, column=0, padx=15, pady=6, sticky="ew")

        # Bottom settings in sidebar
        self.theme_label = ctk.CTkLabel(self.sidebar_frame, text="Tema:", anchor="w")
        self.theme_label.grid(row=8, column=0, padx=20, pady=(10, 0), sticky="w")

        self.theme_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Dark", "Light", "System"],
            command=self._change_appearance_mode,
        )
        self.theme_menu.grid(row=9, column=0, padx=15, pady=(5, 20), sticky="ew")

    # -------------------------------------------------------------
    # Main Content Area
    # -------------------------------------------------------------
    def _build_main_area(self):
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(2, weight=1)

        # Header Title
        self.header_title = ctk.CTkLabel(
            self.main_container,
            text="CKG Umum",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        )
        self.header_title.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # View Frame for Task or Settings
        self.task_view_frame = ctk.CTkFrame(self.main_container)
        self.task_view_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.task_view_frame.grid_columnconfigure(1, weight=1)

        self._build_task_controls()

        # Settings Frame (hidden by default)
        self.settings_frame = ctk.CTkScrollableFrame(self.main_container)
        self._build_settings_controls()

        # Support Frame (hidden by default)
        self.support_frame = ctk.CTkScrollableFrame(self.main_container)
        self._build_support_controls()


        # Log Console Area
        self._build_log_console()

    def _build_task_controls(self):
        # 1. Pilihan Sub-Tugas
        lbl_task = ctk.CTkLabel(self.task_view_frame, text="Pilih Layanan:", font=ctk.CTkFont(weight="bold"))
        lbl_task.grid(row=0, column=0, padx=15, pady=(12, 6), sticky="w")

        self.task_option_menu = ctk.CTkOptionMenu(
            self.task_view_frame,
            values=["Pendaftaran Baru"],
            command=self._on_task_selected,
            width=320,
        )
        self.task_option_menu.grid(row=0, column=1, padx=15, pady=(12, 6), sticky="w")

        # 2. Form Periode Tanggal (Khusus ePuskesmas)
        today_str = datetime.today().strftime("%d-%m-%Y")
        self.epuskesmas_date_frame = ctk.CTkFrame(self.task_view_frame, fg_color="transparent")
        self.epuskesmas_date_frame.grid_columnconfigure(1, weight=1)

        lbl_date = ctk.CTkLabel(self.epuskesmas_date_frame, text="Periode Laporan:", font=ctk.CTkFont(weight="bold"))
        lbl_date.grid(row=0, column=0, padx=(0, 15), pady=4, sticky="w")

        date_inputs = ctk.CTkFrame(self.epuskesmas_date_frame, fg_color="transparent")
        date_inputs.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(date_inputs, text="Dari:").grid(row=0, column=0, padx=(0, 5))
        self.picker_tgl_awal = CTkDatePicker(date_inputs, fg_color="transparent")
        self.picker_tgl_awal.set_date_format("%d-%m-%Y")
        self.picker_tgl_awal.set_date(today_str)
        self.picker_tgl_awal.grid(row=0, column=1, padx=(0, 10))

        ctk.CTkLabel(date_inputs, text="s/d:").grid(row=0, column=2, padx=(0, 5))
        self.picker_tgl_akhir = CTkDatePicker(date_inputs, fg_color="transparent")
        self.picker_tgl_akhir.set_date_format("%d-%m-%Y")
        self.picker_tgl_akhir.set_date(today_str)
        self.picker_tgl_akhir.grid(row=0, column=3, padx=(0, 15))

        btn_today = ctk.CTkButton(
            date_inputs,
            text="Hari Ini",
            width=70,
            height=26,
            command=self._set_date_today,
        )
        btn_today.grid(row=0, column=4, padx=(0, 5))

        btn_yesterday = ctk.CTkButton(
            date_inputs,
            text="H-1 s/d Hari Ini",
            width=110,
            height=26,
            fg_color="gray40",
            hover_color="gray30",
            command=self._set_date_yesterday,
        )
        btn_yesterday.grid(row=0, column=5)

        lbl_date_hint = ctk.CTkLabel(
            self.epuskesmas_date_frame,
            text="*Format: DD-MM-YYYY (Contoh: 13-10-2026). Rentang maksimal 3 hari.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        lbl_date_hint.grid(row=1, column=1, sticky="w", pady=(2, 4))

        # 3. File Excel Dataset
        lbl_dataset = ctk.CTkLabel(self.task_view_frame, text="File Dataset:", font=ctk.CTkFont(weight="bold"))
        lbl_dataset.grid(row=2, column=0, padx=15, pady=6, sticky="w")

        dataset_row = ctk.CTkFrame(self.task_view_frame, fg_color="transparent")
        dataset_row.grid(row=2, column=1, padx=15, pady=6, sticky="ew")
        dataset_row.grid_columnconfigure(0, weight=1)

        default_dataset = str(self.app_root / "dataset" / DEFAULT_COMBINED_WORKBOOK_NAME)
        self.dataset_entry = ctk.CTkEntry(dataset_row, placeholder_text=default_dataset)
        self.dataset_entry.insert(0, default_dataset)
        self.dataset_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        btn_browse = ctk.CTkButton(
            dataset_row,
            text="Pilih File...",
            width=90,
            command=self._browse_excel_file,
        )
        btn_browse.grid(row=0, column=1, padx=(0, 8))

        btn_open_folder = ctk.CTkButton(
            dataset_row,
            text="Buka Folder",
            width=90,
            fg_color="gray40",
            hover_color="gray30",
            command=self._open_dataset_folder,
        )
        btn_open_folder.grid(row=0, column=2)

        # 4. Keterangan Sheet
        self.lbl_sheet_info = ctk.CTkLabel(
            self.task_view_frame,
            text="Sheet yang dibutuhkan: pendaftaran_umum",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        )
        self.lbl_sheet_info.grid(row=3, column=1, padx=15, pady=(0, 8), sticky="w")

        # 5. Action Row (Checkbox + Run Button + Stop Button + Status)
        action_frame = ctk.CTkFrame(self.task_view_frame, fg_color="transparent")
        action_frame.grid(row=4, column=0, columnspan=2, padx=15, pady=(5, 12), sticky="ew")
        action_frame.grid_columnconfigure(3, weight=1)

        self.chk_excel_closed = ctk.CTkCheckBox(
            action_frame,
            text="File Excel sudah disimpan dan ditutup",
        )
        self.chk_excel_closed.select()
        self.chk_excel_closed.grid(row=0, column=0, sticky="w", padx=(0, 15))

        self.btn_run = ctk.CTkButton(
            action_frame,
            text="▶  Mulai Proses",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2b8a3e",
            hover_color="#237032",
            height=36,
            command=self._start_task_execution,
        )
        self.btn_run.grid(row=0, column=1, padx=(0, 8))

        self.btn_stop = ctk.CTkButton(
            action_frame,
            text="⏹  Hentikan",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="gray40",
            hover_color="#c92a2a",
            height=36,
            state="disabled",
            command=self._stop_task_execution,
        )
        self.btn_stop.grid(row=0, column=2, padx=(0, 15))

        self.lbl_status = ctk.CTkLabel(
            action_frame,
            text="Status: Siap",
            font=ctk.CTkFont(weight="bold"),
            text_color="#69db7c",
        )
        self.lbl_status.grid(row=0, column=3, sticky="w")

    def _stop_task_execution(self):
        if self.worker and self.worker.is_running:
            self.lbl_status.configure(text="Status: Dihentikan", text_color="#ffd43b")
            self.btn_run.configure(state="normal", fg_color="#2b8a3e")
            self.btn_stop.configure(state="disabled", fg_color="gray40")
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
        lbl_acc = ctk.CTkLabel(
            self.settings_frame,
            text="Kredensial Akun CKG",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        lbl_acc.pack(anchor="w", padx=10, pady=(10, 5))

        f_acc = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        f_acc.pack(fill="x", padx=10, pady=5)
        f_acc.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(f_acc, text="Username / Email:").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 10))
        self.ent_username = ctk.CTkEntry(f_acc)
        self.ent_username.insert(0, os.getenv(USERNAME_ENV, ""))
        self.ent_username.grid(row=0, column=1, sticky="ew", pady=4)

        ctk.CTkLabel(f_acc, text="Password CKG:").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 10))
        self.ent_password = ctk.CTkEntry(f_acc, show="*")
        self.ent_password.insert(0, os.getenv(PASSWORD_ENV, ""))
        self.ent_password.grid(row=1, column=1, sticky="ew", pady=4)

        btn_save_acc = ctk.CTkButton(
            self.settings_frame,
            text="Simpan Kredensial CKG",
            command=self._save_credentials,
            width=180,
        )
        btn_save_acc.pack(anchor="w", padx=10, pady=(5, 15))

        # Data Wali
        lbl_wali = ctk.CTkLabel(
            self.settings_frame,
            text="Data Wali Fallback (Untuk Pendaftaran Anak/Remaja)",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        lbl_wali.pack(anchor="w", padx=10, pady=(5, 5))

        wali_cfg = get_wali_config()
        self.wali_entries = {}
        f_wali = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        f_wali.pack(fill="x", padx=10, pady=5)
        f_wali.grid_columnconfigure(1, weight=1)

        for i, (key, label) in enumerate(WALI_ENV_KEYS.items()):
            ctk.CTkLabel(f_wali, text=f"{label}:").grid(row=i, column=0, sticky="w", pady=3, padx=(0, 10))
            entry = ctk.CTkEntry(f_wali)
            entry.insert(0, wali_cfg.get(key, ""))
            entry.grid(row=i, column=1, sticky="ew", pady=3)
            self.wali_entries[key] = entry

        btn_save_wali = ctk.CTkButton(
            self.settings_frame,
            text="Simpan Data Wali",
            command=self._save_wali_config,
            width=180,
        )
        btn_save_wali.pack(anchor="w", padx=10, pady=(5, 15))

        # Kredensial ePuskesmas
        lbl_epus = ctk.CTkLabel(
            self.settings_frame,
            text="Kredensial Akun ePuskesmas",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        lbl_epus.pack(anchor="w", padx=10, pady=(5, 5))

        f_epus = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        f_epus.pack(fill="x", padx=10, pady=5)
        f_epus.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(f_epus, text="URL ePuskesmas:").grid(row=0, column=0, sticky="w", pady=4, padx=(0, 10))
        self.ent_epus_url = ctk.CTkEntry(f_epus, placeholder_text="https://situbondo.epuskesmas.id")
        self.ent_epus_url.insert(0, os.getenv(EPUSKESMAS_URL_ENV, ""))
        self.ent_epus_url.grid(row=0, column=1, sticky="ew", pady=4)

        ctk.CTkLabel(f_epus, text="Username:").grid(row=1, column=0, sticky="w", pady=4, padx=(0, 10))
        self.ent_epus_username = ctk.CTkEntry(f_epus)
        self.ent_epus_username.insert(0, os.getenv(EPUSKESMAS_USERNAME_ENV, ""))
        self.ent_epus_username.grid(row=1, column=1, sticky="ew", pady=4)

        ctk.CTkLabel(f_epus, text="Password:").grid(row=2, column=0, sticky="w", pady=4, padx=(0, 10))
        self.ent_epus_password = ctk.CTkEntry(f_epus, show="*")
        self.ent_epus_password.insert(0, os.getenv(EPUSKESMAS_PASSWORD_ENV, ""))
        self.ent_epus_password.grid(row=2, column=1, sticky="ew", pady=4)

        btn_save_epus = ctk.CTkButton(
            self.settings_frame,
            text="Simpan Kredensial ePuskesmas",
            command=self._save_epuskesmas_credentials,
            width=210,
        )
        btn_save_epus.pack(anchor="w", padx=10, pady=(5, 15))

        # Chromium Browser Check
        btn_check_browser = ctk.CTkButton(
            self.settings_frame,
            text="Periksa & Pasang Browser Chromium",
            fg_color="gray40",
            hover_color="gray30",
            command=self._check_and_install_chromium,
            width=240,
        )
        btn_check_browser.pack(anchor="w", padx=10, pady=(5, 15))

    def _build_support_controls(self):
        # 1. Card Pembaruan Aplikasi
        card_update = ctk.CTkFrame(self.support_frame)
        card_update.pack(fill="x", padx=10, pady=(10, 15))
        card_update.grid_columnconfigure(0, weight=1)

        header_update = ctk.CTkFrame(card_update, fg_color="transparent")
        header_update.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 4))
        header_update.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_update,
            text="🔄 Pembaruan Aplikasi",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.btn_check_update = ctk.CTkButton(
            header_update,
            text="🔄 Periksa Pembaruan",
            width=150,
            height=28,
            fg_color="gray40",
            hover_color="gray30",
            command=lambda: self._check_update_async(manual=True),
        )
        self.btn_check_update.grid(row=0, column=1, sticky="e")

        self.lbl_update_status = ctk.CTkLabel(
            card_update,
            text=f"Versi saat ini: v{__version__} • Memeriksa status rilis...",
            wraplength=650,
            justify="left",
            text_color="gray",
        )
        self.lbl_update_status.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 8))

        # Tombol aksi pembaruan (muncul jika update tersedia)
        self.frame_update_actions = ctk.CTkFrame(card_update, fg_color="transparent")
        self.frame_update_actions.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 10))
        self.frame_update_actions.grid_remove()

        self.btn_install_update = ctk.CTkButton(
            self.frame_update_actions,
            text="🚀 Pasang Update Otomatis",
            fg_color="#2b8a3e",
            hover_color="#237032",
            command=self._apply_auto_update,
            width=200,
        )
        self.btn_install_update.pack(side="left", padx=(0, 10))

        self.btn_manual_download = ctk.CTkButton(
            self.frame_update_actions,
            text="🌐 Unduh Manual di GitHub",
            fg_color="#1c7ed6",
            hover_color="#1971c2",
            command=self._open_manual_download,
            width=200,
        )
        self.btn_manual_download.pack(side="left")

        # Catatan rilis / changelog (muncul jika ada)
        self.frame_changelog = ctk.CTkFrame(card_update, fg_color="transparent")
        self.frame_changelog.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 12))
        self.frame_changelog.grid_columnconfigure(0, weight=1)
        self.frame_changelog.grid_remove()

        ctk.CTkLabel(
            self.frame_changelog,
            text="Catatan Rilis (Changelog):",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(0, 4))

        self.txt_changelog = ctk.CTkTextbox(
            self.frame_changelog,
            height=100,
            wrap="word",
            font=ctk.CTkFont(size=12),
        )
        self.txt_changelog.pack(fill="x")
        self.txt_changelog.configure(state="disabled")

        # 2. Card Saweria
        card_saweria = ctk.CTkFrame(self.support_frame)
        card_saweria.pack(fill="x", padx=10, pady=(0, 15))
        card_saweria.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_saweria,
            text="☕ Dukung Pembuat Aplikasi (Saweria)",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(12, 4))

        desc_saweria = (
            "Dukung kami untuk terus mengembangkan aplikasi yang bermanfaat, "
            "Anda dapat melakukan request aplikasi lainnya jika dirasa memang memberikan manfaat bagi banyak orang lainnya."
        )
        ctk.CTkLabel(
            card_saweria,
            text=desc_saweria,
            wraplength=650,
            justify="left",
            text_color="gray",
        ).grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))

        f_saweria_btn = ctk.CTkFrame(card_saweria, fg_color="transparent")
        f_saweria_btn.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 12))

        btn_saweria = ctk.CTkButton(
            f_saweria_btn,
            text="☕ Buka Saweria (saweria.co/stywn93)",
            fg_color="#e8590c",
            hover_color="#d9480f",
            command=self._open_saweria,
            width=240,
        )
        btn_saweria.pack(side="left", padx=(0, 10))

        btn_copy_saweria = ctk.CTkButton(
            f_saweria_btn,
            text="Salin Tautan Saweria",
            fg_color="gray40",
            hover_color="gray30",
            command=self._copy_saweria_link,
            width=160,
        )
        btn_copy_saweria.pack(side="left")

        # 3. Card Telegram
        card_tele = ctk.CTkFrame(self.support_frame)
        card_tele.pack(fill="x", padx=10, pady=(0, 15))
        card_tele.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_tele,
            text="💬 Kontak & Bantuan Otomasi (Telegram)",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(12, 4))

        desc_tele = (
            "Mengalami kendala teknis, punya ide/saran pengembangan fitur baru, "
            "atau membutuhkan konsultasi integrasi otomasi kesehatan lainnya? "
            "Silakan hubungi langsung pengembang melalui Telegram."
        )
        ctk.CTkLabel(
            card_tele,
            text=desc_tele,
            wraplength=650,
            justify="left",
            text_color="gray",
        ).grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))

        f_tele_btn = ctk.CTkFrame(card_tele, fg_color="transparent")
        f_tele_btn.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 12))

        btn_tele = ctk.CTkButton(
            f_tele_btn,
            text="💬 Hubungi via Telegram (@stywn93)",
            fg_color="#1c7ed6",
            hover_color="#1971c2",
            command=self._open_telegram,
            width=240,
        )
        btn_tele.pack(side="left", padx=(0, 10))

        btn_copy_tele = ctk.CTkButton(
            f_tele_btn,
            text="Salin Username Telegram",
            fg_color="gray40",
            hover_color="gray30",
            command=self._copy_telegram_handle,
            width=180,
        )
        btn_copy_tele.pack(side="left")

        # 4. Card Tentang Aplikasi
        card_about = ctk.CTkFrame(self.support_frame)
        card_about.pack(fill="x", padx=10, pady=(0, 10))
        card_about.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_about,
            text="ℹ️ Tentang CKG Helper",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(12, 4))

        about_text = (
            f"CKG Helper v{__version__}\n"
            "Aplikasi Otomasi Pendaftaran & Pelaporan Cek Kesehatan Gratis (CKG) serta Integrasi ePuskesmas BPJS.\n"
            "Dibuat untuk memudahkan tenaga kesehatan dan operator faskes dalam penginputan data."
        )
        ctk.CTkLabel(
            card_about,
            text=about_text,
            wraplength=650,
            justify="left",
            text_color="gray",
        ).grid(row=1, column=0, sticky="w", padx=15, pady=(0, 12))

    def _check_update_async(self, manual: bool = False):
        if self.is_checking_update:
            return
        self.is_checking_update = True
        self.btn_check_update.configure(state="disabled", text="Memeriksa...")
        self.lbl_update_status.configure(
            text=f"Versi saat ini: v{__version__} • Sedang memeriksa pembaruan dari GitHub...",
            text_color="gray",
        )

        def worker():
            info = check_for_update()

            def update_ui():
                self.is_checking_update = False
                self.btn_check_update.configure(state="normal", text="🔄 Periksa Pembaruan")
                self.update_info = info
                if info:
                    self.lbl_update_status.configure(
                        text=f"🎉 Versi baru tersedia: {info['version']}! (Versi Anda: v{__version__})",
                        text_color="#69db7c",
                    )
                    self.btn_support.configure(text="💖  Support & Donasi 🟢")
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
                    self.lbl_update_status.configure(
                        text=f"✅ Aplikasi sudah menggunakan versi terbaru (v{__version__}).",
                        text_color="#69db7c",
                    )
                    self.btn_support.configure(text="💖  Support & Donasi")
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
        self.console_container = ctk.CTkFrame(self.main_container)
        self.console_container.grid(row=2, column=0, sticky="nsew")
        self.console_container.grid_columnconfigure(0, weight=1)
        self.console_container.grid_rowconfigure(1, weight=1)

        # Header Console
        console_header = ctk.CTkFrame(self.console_container, fg_color="transparent", height=32)
        console_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        console_header.grid_columnconfigure(0, weight=1)

        lbl_console = ctk.CTkLabel(
            console_header,
            text="Terminal Output / Live Log",
            font=ctk.CTkFont(weight="bold"),
        )
        lbl_console.grid(row=0, column=0, sticky="w")

        btn_copy = ctk.CTkButton(
            console_header,
            text="Salin Log",
            width=70,
            height=24,
            command=self._copy_log,
        )
        btn_copy.grid(row=0, column=1, padx=(0, 6))

        btn_clear = ctk.CTkButton(
            console_header,
            text="Bersihkan",
            width=70,
            height=24,
            fg_color="gray40",
            hover_color="gray30",
            command=self._clear_log,
        )
        btn_clear.grid(row=0, column=2)

        # Textbox
        self.log_textbox = ctk.CTkTextbox(
            self.console_container,
            wrap="char",
            font=ctk.CTkFont(family="Courier", size=12),
        )
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))


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
        self.header_title.configure(text="Support & Donasi" if category == "Support" else category)

        # Style active sidebar button
        buttons = {
            "CKG Umum": self.btn_umum,
            "CKG Sekolah": self.btn_sekolah,
            "ePuskesmas": self.btn_epuskesmas,
            "Pengaturan": self.btn_settings,
            "Support": self.btn_support,
        }
        for name, btn in buttons.items():
            if name == category:
                btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
            else:
                btn.configure(fg_color="transparent")

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
            self.task_view_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
            self.console_container.grid(row=2, column=0, sticky="nsew")
            if category == "ePuskesmas":
                self.epuskesmas_date_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=4, sticky="ew")
            else:
                self.epuskesmas_date_frame.grid_remove()
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
        cfg = {k: self.wali_entries[k].get().strip() for k in WALI_ENV_KEYS}
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
            self.lbl_status.configure(text="Status: Mengunduh Chromium...", text_color="#ffd43b")
            self.btn_run.configure(state="disabled")

            def do_install():
                code = run_playwright_cli(["install", "chromium"])
                if code == 0:
                    self.after(0, lambda: messagebox.showinfo("Sukses", "Chromium berhasil dipasang."))
                    self.after(0, lambda: self.lbl_status.configure(text="Status: Siap", text_color="#69db7c"))
                else:
                    self.after(0, lambda: messagebox.showerror("Gagal", "Gagal mengunduh Chromium."))
                    self.after(0, lambda: self.lbl_status.configure(text="Status: Error Browser", text_color="#fa5252"))
                self.after(0, lambda: self.btn_run.configure(state="normal"))

            import threading
            threading.Thread(target=do_install, daemon=True).start()

    def _change_appearance_mode(self, mode: str):
        ctk.set_appearance_mode(mode)

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
        self.btn_run.configure(state="disabled", fg_color="gray40")
        self.btn_stop.configure(state="normal", fg_color="#c92a2a")
        self.lbl_status.configure(text="Status: Berjalan...", text_color="#ffd43b")

        def on_started():
            pass

        def on_finished(success: bool, msg: str):
            def update_ui():
                self.btn_run.configure(state="normal", fg_color="#2b8a3e")
                self.btn_stop.configure(state="disabled", fg_color="gray40")
                if success:
                    self.lbl_status.configure(text="Status: Selesai", text_color="#69db7c")
                else:
                    if "dihentikan" in msg.lower():
                        self.lbl_status.configure(text="Status: Dihentikan", text_color="#ffd43b")
                    else:
                        self.lbl_status.configure(text="Status: Gagal", text_color="#fa5252")
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
