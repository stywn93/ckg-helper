# CKG-Helper

CKG-Helper adalah tool otomatisasi untuk skrining kesehatan pada platform Sehat Indonesia Ku (CKG) milik Kementerian Kesehatan Indonesia. Tool ini menggunakan Playwright untuk mengotomatisasi proses skrining kesehatan untuk berbagai kategori pasien.

## Beta: Penggunaan Tanpa Install Python

Untuk pengguna non-teknis, gunakan paket beta hasil build untuk Windows atau macOS. Pengguna cukup menjalankan aplikasi terminal dan memilih menu.

Menu yang tersedia:

```text
1. Pendaftaran Baru
2. Konfirmasi Kehadiran
3. CKG Umum Anak
4. CKG Umum Remaja
5. CKG Umum Dewasa
6. CKG Umum Lansia
0. Keluar
```

Isi folder release:

```text
ckg-helper atau ckg-helper.exe
Jalankan CKG Helper.command / Jalankan CKG Helper.bat
dataset/
.env.example
browsers/          (dibuat otomatis saat pertama kali download Chromium)
.env               (dibuat otomatis saat pertama kali login)
```

Cara menjalankan:

- **Cara termudah:** double-click `Jalankan CKG Helper.command` (macOS) atau `Jalankan CKG Helper.bat` (Windows)
- Windows (manual): buka Command Prompt atau PowerShell di folder release, lalu jalankan `.\ckg-helper.exe`
- macOS (manual): buka Terminal di folder release, lalu jalankan `./ckg-helper`

Saat pertama kali dijalankan:

- Jika file `.env` belum ada, aplikasi akan meminta username dan password CKG lalu menyimpannya di `.env`.
- Jika Chromium Playwright belum terpasang, aplikasi akan meminta izin untuk mengunduh Chromium otomatis satu kali.
- File Excel harus berada di folder `dataset/` yang satu folder dengan aplikasi.
- Kolom `status` pada Excel akan diperbarui selama proses berjalan.

Catatan beta:

- Paket Windows dan macOS harus dibuat terpisah pada sistem operasi masing-masing.
- Download Chromium pertama kali membutuhkan koneksi internet dan disimpan di folder `browsers/` pada folder aplikasi.
- Jangan buka file Excel yang sedang diproses di Microsoft Excel/Numbers karena aplikasi perlu menulis status ke file tersebut.

### Troubleshooting rilis

**macOS — aplikasi tidak bisa dibuka (Gatekeeper)**

Jika macOS memblokir aplikasi dari developer tidak dikenal:

1. Buka Terminal di folder `dist/`
2. Jalankan: `xattr -cr "Jalankan CKG Helper.command" ckg-helper`
3. Coba double-click launcher lagi

Atau: System Settings → Privacy & Security → Allow.

**Windows — SmartScreen memblokir**

Klik "More info" → "Run anyway" pada peringatan SmartScreen.

**Download Chromium gagal**

Periksa koneksi internet, proxy/firewall kantor, atau antivirus. Hapus folder `browsers/` lalu jalankan ulang dan pilih download lagi.

## 📋 Fitur

- **Otomatisasi Skrining Kesehatan**: Mengotomatisasi proses skrining untuk berbagai kategori pasien
- **Multi-Kategori Pasien**: Mendukung skrining untuk Anak, Remaja, Dewasa, dan Lansia
- **Skrining Mandiri & Nakes**: Mendukung dua jenis skrining - skrining mandiri dan skrining oleh tenaga kesehatan
- **Integrasi Excel**: Data pasien diambil dari file Excel dan status skrining dicatat kembali
- **Error Handling**: Mekanisme error handling yang baik dengan pencatatan status di Excel
- **Timeout Management**: Konfigurasi timeout yang dapat disesuaikan untuk elemen UI

## 🏗️ Struktur Project

```
CKG-Helper/
├── .env                    # Environment variables (credentials)
├── .env.example            # Template environment variables
├── requirements.txt        # Python dependencies
├── dataset/                # Folder untuk file Excel data pasien
│   ├── anak.xlsx          # Data pasien anak
│   ├── dewasa.xlsx        # Data pasien dewasa
│   ├── lansia.xlsx        # Data pasien lansia
│   ├── remaja.xlsx        # Data pasien remaja
│   └── ...                # File Excel lainnya
└── src/
    ├── ckg-umum/          # Script utama untuk setiap kategori pasien
    │   ├── anak.py        # Script skrining pasien anak
    │   ├── dewasa.py      # Script skrining pasien dewasa
    │   ├── lansia.py      # Script skrining pasien lansia
    │   ├── remaja.py      # Script skrining pasien remaja
    │   ├── daftar_baru.py # Script pendaftaran pasien baru
    │   ├── konfirm_kehadiran.py # Script konfirmasi kehadiran
    │   └── playwright_window_layout.py # Konfigurasi window layout
    └── helpers/           # Helper functions dan classes
        ├── excel.py       # Class untuk handling Excel
        ├── date_picker.py # Helper untuk date picker
        ├── screening_mandiri.py # Class untuk skrining mandiri
        └── screening_nakes.py    # Class untuk skrining oleh nakes
```

## Build Paket Beta

Install dependency build:

```bash
pip install -r requirements-build.txt
```

Build macOS:

```bash
./scripts/build_macos.sh
```

Build Windows:

```powershell
.\scripts\build_windows.ps1
```

Hasil build ada di folder `dist/`. Folder `dataset/` akan disalin ke `dist/dataset/` supaya file Excel tetap bisa diedit dan ditulis statusnya.

## 🚀 Instalasi Developer

### Prasyarat

- Python 3.8 atau lebih tinggi
- pip (package manager Python)

### Langkah-langkah Instalasi

1. Clone repository ini:
```bash
git clone <repository-url>
cd CKG-Helper
```

2. Buat virtual environment (opsional tapi disarankan):
```bash
python -m venv .venv
source .venv/bin/activate  # Untuk Linux/Mac
.venv\Scripts\activate     # Untuk Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install chromium
```

## ⚙️ Konfigurasi

1. Copy file `.env.example` ke `.env`:
```bash
cp .env.example .env
```

2. Edit file `.env` dan isi dengan kredensial Anda:
```env
CKG_USERNAME=email_anda
CKG_PASSWORD=password_anda
```

3. (Opsional) Tambahkan konfigurasi tambahan:
```env
CKG_SCREENING_UI_TIMEOUT_MS=5000  # Timeout untuk elemen UI (default: 2000-5000 ms)
CKG_DEBUG_RAISE_ERRORS=0          # Set ke 1 untuk raise errors saat debugging
```

## 📖 Penggunaan Developer

### Launcher Terminal

```bash
python ckg_helper.py
```

### Menjalankan Skrining untuk Setiap Kategori

#### Skrining Pasien Anak
```bash
python src/ckg-umum/anak.py
```

#### Skrining Pasien Dewasa
```bash
python src/ckg-umum/dewasa.py
```

#### Skrining Pasien Lansia
```bash
python src/ckg-umum/lansia.py
```

#### Skrining Pasien Remaja
```bash
python src/ckg-umum/remaja.py
```

### Menyiapkan Data Pasien

1. Siapkan file Excel di folder `dataset/` sesuai kategori pasien
2. Pastikan file Excel memiliki kolom yang sesuai dengan kebutuhan skrining
3. Kolom `status` akan ditambahkan secara otomatis untuk tracking status skrining

### Status Skrining

Status skrining akan dicatat di kolom `status` pada file Excel:
- `SUCCESS` - Skrining berhasil dilakukan
- `FAILED: [error message]` - Skrining gagal dengan pesan error
- Kosong - Belum diproses

### Pilihan Status Pemeriksaan

Saat menjalankan script, Anda akan diminta untuk memilih status pemeriksaan:
1. Belum Pemeriksaan
2. Sedang Pemeriksaan
3. Selesai Pemeriksaan

## 🧪 Jenis Skrining

### Skrining Mandiri

Skrining yang diisi oleh pasien sendiri, mencakup:
- Demografi
- Risiko penyakit (malaria, TB, hepatitis, dll)
- Perilaku kesehatan (merokok, aktivitas fisik)
- Kesehatan jiwa

### Skrining oleh Nakes

Skrining yang dilakukan oleh tenaga kesehatan, mencakup:
- Pemeriksaan fisik (berat badan, tinggi badan, tekanan darah)
- Pemeriksaan laboratorium (gula darah, lipid, dll)
- Pemeriksaan khusus (mata, telinga, gigi)
- Skrining penyakit menular

## 📦 Dependencies

- `playwright==1.60.0` - Browser automation framework
- `openpyxl` - Library untuk membaca/menulis file Excel
- `python-dotenv` - Library untuk memuat environment variables dari .env file

## 🔧 Troubleshooting

### Playwright Browser Tidak Terinstall
Jika mendapatkan error tentang browser tidak ditemukan:
```bash
playwright install chromium
```

### Timeout Error
Jika sering mendapatkan timeout error, tingkatkan nilai `CKG_SCREENING_UI_TIMEOUT_MS` di file `.env`:
```env
CKG_SCREENING_UI_TIMEOUT_MS=10000
```

### Login Gagal
Pastikan kredensial di file `.env` sudah benar dan akun memiliki akses ke sistem CKG.

### Excel File Locked
Pastikan file Excel tidak sedang dibuka di aplikasi lain saat script berjalan.

## 🤝 Kontribusi

Kontribusi sangat diapresiasi! Silakan:
1. Fork repository
2. Buat branch untuk fitur baru (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buka Pull Request

## 📝 Catatan Penting

- Tool ini hanya boleh digunakan untuk tujuan yang sah dan sesuai dengan kebijakan Kementerian Kesehatan Indonesia
- Pastikan untuk memiliki izin dan akses yang sesuai sebelum menggunakan tool ini
- Tool ini mengotomatisasi interaksi dengan web, perubahan pada UI web dapat menyebabkan script tidak berfungsi
- Selalu backup file Excel sebelum menjalankan script

## 📄 Lisensi

Project ini dibuat untuk keperluan internal dan tidak memiliki lisensi publik.

## 📞 Kontak

Untuk pertanyaan atau masalah, silakan hubungi tim pengembang atau buka issue di repository.

---

**Disclaimer**: Tool ini adalah tool otomatisasi dan bukan produk resmi dari Kementerian Kesehatan Indonesia. Gunakan dengan tanggung jawab dan sesuai dengan aturan yang berlaku.
