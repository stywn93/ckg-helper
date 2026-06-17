# Analisis Kolom Excel Unused pada dataset/lansia.xlsx

Dokumen ini berisi hasil analisis perbandingan antara kolom header di file Excel `dataset/lansia.xlsx` dengan data field yang diakses oleh script pelayanan lansia (`src/ckg-umum/lansia.py`) beserta helper screening yang dipanggil (`src/helpers/screening_mandiri.py` dan `src/helpers/screening_nakes.py`).

---

## Metodologi
Kami menganalisis struktur data pada file Excel `dataset/lansia.xlsx` (total 206 kolom) dan membandingkannya dengan field dictionary `data[...]` yang digunakan dalam flow program:
1. **Fungsi Skrining Mandiri Lansia** pada `lansia.py`.
2. **Fungsi Skrining Nakes Lansia** (untuk Laki-laki dan Perempuan) pada `lansia.py`.
3. **Flow Utama/Metadata** di `lansia.py` (seperti pencarian pasien dan status baris).

---

## Hasil Analisis Kolom

### 1. Kolom yang Tidak Digunakan (Unused Columns)
Ditemukan **26 kolom** dari total 206 kolom di `dataset/lansia.xlsx` yang **tidak dipanggil/diakses** oleh logika skrining lansia maupun flow script utama:

| No. Kolom (1-Based) | Nama Kolom | Keterangan |
|---------------------|------------|------------|
| **Kolom 4** | `nik` | Logika `search_patient` pada `lansia.py` menggunakan kolom `nama` (`data["nama"]`), bukan NIK. |
| **Kolom 6** | `rencana_menikah` | Skrining demografi lansia (`do_demografi_lansia`) hanya mencakup `status_perkawinan` dan `disabilitas`. |
| **Kolom 7** | `sedang_hamil` | Logika kehamilan tidak diperiksa pada lansia. |
| **Kolom 21** | `pernah_seks` | Skrining kanker leher rahim (`do_leher_rahim`) tidak dijalankan untuk kategori lansia. |
| **Kolom 58** | *None* (Kosong) | Kolom tanpa header / kosong. |
| **Kolom 59 s.d. 197** (21 Kolom) | `periksa_...` | Kolom penanda check-box pemeriksaan di Excel (seperti `periksa_gizi_laki`, `periksa_gula_darah`, `periksa_tensi`, `periksa_tbc`, dsb.) diabaikan karena script otomasi langsung mengeksekusi semua modul skrining lansia tanpa memeriksa checkbox penanda tersebut terlebih dahulu. |

---

### 2. Kolom yang Digunakan (Used Columns)
Sebanyak **180 kolom** sisanya digunakan secara aktif untuk mendukung pengisian modul skrining khusus Lansia (SKILAS kognitif, SKILAS mobilisasi, SKILAS malnutrisi, SKILAS depresi, gangguan fungsional ADL, Mini-Cog, AD8 Indonesia, SPPB mobilisasi lanjutan, MNA malnutrisi lanjutan, GDS depresi lanjutan), skrining umum dewasa, dan flow script utama (`batas_awal`, `batas_akhir`, `nama`, `status`).
