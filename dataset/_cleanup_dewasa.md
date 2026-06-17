# Analisis Kolom Excel Unused pada dataset/dewasa.xlsx

Dokumen ini berisi hasil analisis perbandingan antara kolom header di file Excel `dataset/dewasa.xlsx` dengan data field yang diakses oleh script pelayanan dewasa (`src/ckg-umum/dewasa.py`) beserta helper screening yang dipanggil (`src/helpers/screening_mandiri.py` dan `src/helpers/screening_nakes.py`).

---

## Metodologi
Kami menganalisis struktur data pada file Excel `dataset/dewasa.xlsx` (total 178 kolom) dan membandingkannya dengan field dictionary `data[...]` yang digunakan dalam flow program:
1. **Fungsi Skrining Mandiri Dewasa** (untuk Laki-laki dan Perempuan) pada `dewasa.py`.
2. **Fungsi Skrining Nakes Dewasa** (untuk Laki-laki dan Perempuan) pada `dewasa.py`.
3. **Flow Utama/Metadata** di `dewasa.py` (seperti pencarian pasien dan status baris).

---

## Hasil Analisis Kolom

### 1. Kolom yang Tidak Digunakan (Unused Columns)
Ditemukan **25 kolom** dari total 178 kolom di `dataset/dewasa.xlsx` yang **tidak dipanggil/diakses** oleh logika skrining dewasa maupun flow script utama:

| No. Kolom (1-Based) | Nama Kolom | Alasan / Keterangan |
|---------------------|------------|---------------------|
| **Kolom 4** | `nik` | Logika `search_patient` pada `dewasa.py` melakukan pencarian pasien menggunakan nilai dari kolom `nama` (`data["nama"]`), bukan NIK. |
| **Kolom 40** | `imunisasi_tetanus` | Tidak dipanggil oleh method `do_imunisasi_tetanus` (yang secara keliru memetakan input kesehatan jiwa). |
| **Kolom 59** | `periksa_gizi_laki` | Kolom indikator pemeriksaan ini dilewati karena script langsung menjalankan fungsi pemeriksaan gizi. |
| **Kolom 63** | `periksa_gula_darah` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 70** | `periksa_tensi` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 77** | `periksa_risiko_tbc` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 85** | `periksa_tbc` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 90** | `periksa_frambusia` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 93** | `periksa_kusta` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 96** | `periksa_skabies` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 98** | `periksa_telinga_mata` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 109** | `periksa_karies` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 112** | `periksa_periodontal` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 115** | `periksa_ppok` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 122** | `periksa_co` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 124** | `periksa_lipid` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 129** | `periksa_fibrosis` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 132** | `periksa_hepatitis` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 136** | `periksa_fungsi_ginjal` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 141** | `periksa_kerusakan_ginjal` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 154** | `periksa_jantung` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 157** | `periksa_kanker_usus` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 161** | `periksa_kanker_paru` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 171** | `periksa_hiv` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 176** | `periksa_sifilis` | Kolom indikator pemeriksaan dilewati. |

> [!TIP]
> Kolom dengan awalan `periksa_...` (seperti `periksa_tensi`, `periksa_kusta`, dll.) adalah kolom penanda/check-box di Excel. Program tidak mengecek kolom ini sebelum melakukan skrining, melainkan menjalankan setiap skrining secara langsung (unconditional) jika elemen UI-nya ditemukan. Oleh karena itu, kolom-kolom penanda tersebut bersifat *redundant*/tidak terpakai oleh sistem otomasi.

---

### 2. Kolom yang Digunakan (Used Columns)
Sebanyak **153 kolom** sisanya digunakan secara aktif untuk mengisi form skrining Mandiri dan Nakes Dewasa, serta flow script utama (`batas_awal`, `batas_akhir`, `nama`, `status`). 
