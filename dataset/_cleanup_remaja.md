# Analisis Kolom Excel Unused pada dataset/remaja.xlsx

Dokumen ini berisi hasil analisis perbandingan antara kolom header di file Excel `dataset/remaja.xlsx` dengan data field yang diakses oleh script pelayanan remaja (`src/ckg-umum/remaja.py`) beserta helper screening yang dipanggil (`src/helpers/screening_mandiri.py` dan `src/helpers/screening_nakes.py`).

---

## Metodologi
Kami menganalisis struktur data pada file Excel `dataset/remaja.xlsx` (total 67 kolom) dan membandingkannya dengan field dictionary `data[...]` yang digunakan dalam flow program:
1. **Fungsi Skrining Mandiri** yang terdaftar di `TEENAGER_MANDIRI_SCREENINGS` pada `src/ckg-umum/remaja.py`.
2. **Fungsi Skrining Nakes** yang terdaftar di `TEENAGER_NAKES_SCREENINGS` pada `src/ckg-umum/remaja.py`.
3. **Flow Utama/Metadata** di `remaja.py` (seperti pencarian pasien dan status baris).

---

## Hasil Analisis Kolom

### 1. Kolom yang Tidak Digunakan (Unused Columns)
Berikut adalah daftar kolom di `dataset/remaja.xlsx` yang **tidak dipanggil** oleh logika skrining remaja maupun flow script utama:

| No. Kolom (1-Based) | Nama Kolom | Keterangan |
|---------------------|------------|------------|
| **Kolom 4**         | `nik`      | Tidak digunakan. Di dalam flow `search_patient` pada `remaja.py`, kolom pencarian pasien diisi menggunakan nilai dari kolom `nama` (`data["nama"]`), bukan NIK. |
| **Kolom 27**        | *None* (Kosong) | Kolom tanpa header / kosong. |
| **Kolom 46**        | *None* (Kosong) | Kolom tanpa header / kosong. |
| **Kolom 54**        | *None* (Kosong) | Kolom tanpa header / kosong. |

> [!NOTE]
> Kolom metadata berikut **tidak digunakan di form skrining** namun **tetap digunakan oleh flow program**, sehingga **tidak boleh dihapus**:
> - `batas_awal` (Kolom 1) - Untuk filter pencarian tanggal mulai.
> - `batas_akhir` (Kolom 2) - Untuk filter pencarian tanggal akhir.
> - `nama` (Kolom 3) - Untuk kata kunci pencarian pasien.
> - `status` (Kolom 67) - Untuk penanda status pemrosesan baris.

---

### 2. Temuan dan Catatan Tambahan

* **Duplikasi Header (`berapa_bulan_diabetes`)**:
  Ditemukan nama kolom yang sama pada dua posisi berbeda:
  - **Kolom 6**: `berapa_bulan_diabetes` (digunakan pada `do_risiko_gula_darah_anak` di Skrining Mandiri).
  - **Kolom 33**: `berapa_bulan_diabetes` (digunakan pada `do_gula_darah_anak` di Skrining Nakes).
  
  Meskipun keduanya digunakan, memiliki nama kolom duplikat dalam struktur baris/dictionary dapat menimbulkan risiko data tertimpa (overwrite) tergantung cara parser Excel memetakan sheet ke dictionary Python. Disarankan untuk membedakan nama kolom jika memungkinkan (misalnya `berapa_bulan_diabetes_mandiri` dan `berapa_bulan_diabetes_nakes`).
