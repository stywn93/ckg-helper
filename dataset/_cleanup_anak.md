# Analisis Kolom Excel Unused pada dataset/anak.xlsx

Dokumen ini berisi hasil analisis perbandingan antara kolom header di file Excel `dataset/anak.xlsx` dengan data field yang diakses oleh script pelayanan anak (`src/ckg-umum/anak.py`) beserta helper screening yang dipanggil (`src/helpers/screening_mandiri.py` dan `src/helpers/screening_nakes.py`).

---

## Metodologi
Kami menganalisis struktur data pada file Excel `dataset/anak.xlsx` (total 136 kolom) dan membandingkannya dengan field dictionary `data[...]` yang digunakan dalam flow program:
1. **Fungsi Skrining Mandiri Anak** pada `anak.py`.
2. **Fungsi Skrining Nakes Anak** pada `anak.py`.
3. **Flow Utama/Metadata** di `anak.py` (seperti pencarian pasien dan status baris).

---

## Hasil Analisis Kolom

### 1. Kolom yang Tidak Digunakan (Unused Columns)
Ditemukan **56 kolom** dari total 136 kolom di `dataset/anak.xlsx` yang **tidak dipanggil/diakses** oleh logika skrining anak maupun flow script utama:

| No. Kolom (1-Based) | Nama Kolom | Keterangan |
|---------------------|------------|------------|
| **Kolom 4** | `nik` | Logika `search_patient` pada `anak.py` menggunakan kolom `nama` (`data["nama"]`), bukan NIK. |
| **Kolom 66** | `periksa_tbc` | Kolom indikator pemeriksaan (checkbox di Excel) dilewati. |
| **Kolom 71** | `periksa_frambusia` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 74** | `periksa_kusta` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 77** | `periksa_skabies` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 79** | `periksa_telinga_mata` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 85** | `periksa_gigi_anak` | Kolom indikator pemeriksaan dilewati. |
| **Kolom 87** | `gigi_hilang` | Tidak digunakan di skrining gigi anak (hanya menggunakan `jumlah_gigi_karies`). |
| **Kolom 88** | `periksa_periodontal` | Skrining dewasa/lansia, tidak dilakukan pada anak. |
| **Kolom 89** | `penyakit_periodontal` | Skrining dewasa/lansia, tidak dilakukan pada anak. |
| **Kolom 90** | `gigi_goyang` | Skrining dewasa/lansia, tidak dilakukan pada anak. |
| **Kolom 91 s.d. 135** | `periksa_ppok`, `ppok_merokok`, `bungkus_per_tahun`, `nafas_pendek`, `mempunyai_dahak`, `batuk_tanpa_flu`, `periksa_spirometri`, `periksa_co`, `kadar_co`, `periksa_lipid`, `kolesterol`, `hdl`, `ldl`, `trigliserida`, `periksa_fibrosis`, `sgot`, `trombosit`, `periksa_hepatitis`, `hepatitis_b`, `hepatitis_c`, `vl_hepatitis_c`, `periksa_fungsi_ginjal`, `kreatinin`, `ureum`, `usia`, `e_lfg`, `periksa_kerusakan_ginjal`, `albumin`, `kreatinin_urin`, `periksa_jantung`, `ekg`, `pemeriksaan_ekg`, `periksa_kanker_usus`, `bersedia_colok_dubur`, `colok_dubur`, `darah_samar`, `periksa_kanker_paru`, `kanker_paru`, `keluarga_kanker`, `riwayat_merokok`, `tempat_kerja_karsinogenik`, `tempat_tinggal_potensi_tinggi`, `lingkungan_tidak_sehat`, `penyakit_paru_kronik`, `foto_torax` | Kolom pemeriksaan PPOK, Jantung, Ginjal, Lipid, Fibrosis, Hepatitis, serta Kanker Usus/Paru adalah bagian skrining dewasa/lansia yang tidak dilakukan pada kategori anak. |

> [!NOTE]
> Kolom indikator check-box `periksa_...` diabaikan karena script otomasi secara langsung mengeksekusi fungsi skrining anak yang relevan tanpa memeriksa penanda checkbox tersebut terlebih dahulu di file Excel.

---

### 2. Kolom yang Digunakan (Used Columns)
Sebanyak **80 kolom** sisanya digunakan secara aktif untuk merekam status demografi anak, riwayat imunisasi, pertumbuhan balita, KPSP, M-CHAT, skrining penyakit anak (TB anak, frambusia, kusta, skabies, kesehatan mata & telinga anak), serta flow script utama (`batas_awal`, `batas_akhir`, `nama`, `status`).
