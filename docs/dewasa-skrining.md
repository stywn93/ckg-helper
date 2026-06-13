# Dokumentasi Teknis Skrining Dewasa

Dokumen ini menjelaskan peran `src/ckg-umum/dewasa.py` dalam otomatisasi CKG untuk kategori pasien dewasa, termasuk korelasinya dengan skrining mandiri dan skrining nakes.

## Tujuan Modul

`dewasa.py` membaca antrean pasien dari `dataset/dewasa.xlsx`, membuka halaman pelayanan CKG, mencari pasien berdasarkan data Excel, lalu menjalankan formulir skrining dewasa sesuai badge kategori dan jenis kelamin yang tampil di UI.

Output utama proses adalah update kolom `status` di workbook:

- `SUCCESS` untuk pasien dewasa yang selesai diproses.
- `Gagal - ini bukan pasien dewasa...` jika badge kategori pasien bukan `Dewasa`.
- `FAILED: ...` jika terjadi exception saat memproses baris.

## Alur Eksekusi

1. `main()` memuat konfigurasi dari `.env`, membuka `dataset/dewasa.xlsx`, dan mengambil baris yang belum berstatus sukses.
2. Playwright membuka halaman `https://sehatindonesiaku.kemkes.go.id/ckg-pelayanan`.
3. Script login menggunakan `CKG_USERNAME` dan `CKG_PASSWORD`.
4. Untuk setiap baris Excel, `search_patient()` menyiapkan halaman pelayanan, memilih status `Sedang Pemeriksaan`, memilih rentang tanggal, mencari pasien, lalu masuk ke halaman pemeriksaan.
5. Script membaca badge kategori pasien dari UI. Jika badge bukan `Dewasa`, baris Excel ditandai gagal dan proses lanjut ke baris berikutnya.
6. Jika badge `Dewasa`, script membaca jenis kelamin pasien dari UI.
7. Berdasarkan jenis kelamin, script menjalankan skrining mandiri terlebih dahulu, lalu skrining nakes.
8. Jika seluruh tahap selesai tanpa exception, status baris Excel diubah menjadi `SUCCESS`.

## Korelasi dengan Skrining Mandiri

Skrining mandiri dijalankan melalui class `ScreeningMandiri` dari `src/helpers/screening_mandiri.py`.

Pada pasien dewasa laki-laki, urutan method diambil dari `DEWASA_MANDIRI_LAKI_SCREENINGS`:

```python
[
    "do_demografi_dewasa",
    "do_risiko_kanker_usus",
    "do_risiko_tb",
    "do_hati",
    "do_keswa",
    "do_risiko_kanker_paru",
    "do_perilaku_merokok",
    "do_aktivitas_fisik",
]
```

Pada pasien dewasa perempuan, urutan method diambil dari `DEWASA_MANDIRI_PEREMPUAN_SCREENINGS`:

```python
[
    "do_demografi_dewasa_perempuan",
    "do_risiko_kanker_usus",
    "do_risiko_tb",
    "do_hati",
    "do_leher_rahim",
    "do_keswa",
    "do_risiko_kanker_paru",
    "do_perilaku_merokok",
    "do_aktivitas_fisik",
]
```

Secara domain, tahap ini mengisi form yang berasal dari jawaban pasien atau self-assessment, seperti demografi, faktor risiko penyakit, kesehatan jiwa, perilaku merokok, dan aktivitas fisik. Skrining mandiri dijalankan lebih dulu agar data self-assessment tersedia sebelum pemeriksaan nakes dilanjutkan.

## Korelasi dengan Skrining Nakes

Skrining nakes dijalankan melalui class `ScreeningNakes` dari `src/helpers/screening_nakes.py`.

Pada pasien dewasa laki-laki, urutan method diambil dari `DEWASA_NAKES_LAKI_SCREENINGS`:

```python
[
    "do_gizi_laki",
    "do_gula_darah_dewasa",
    "do_tekanan_darah_dewasa",
    "do_risiko_tb",
    "do_tb",
    "do_frambusia",
    "do_kusta",
    "do_skabies",
    "do_telinga_mata",
    "do_karies",
    "do_periodontal",
    "do_ppok",
    "do_kadar_co",
    "do_lipid",
    "do_fibrosis",
    "do_hepatitis",
    "do_fungsi_ginjal",
    "do_kerusakan_ginjal",
    "do_jantung",
    "do_kanker_usus",
    "do_kanker_paru",
    "do_hiv",
    "do_sifilis",
]
```

Pada pasien dewasa perempuan, urutan method diambil dari `DEWASA_NAKES_PEREMPUAN_SCREENINGS`:

```python
[
    "do_gizi_perempuan",
    "do_gula_darah_dewasa",
    "do_tekanan_darah_dewasa",
    "do_risiko_tb",
    "do_tb",
    "do_frambusia",
    "do_kusta",
    "do_skabies",
    "do_telinga_mata",
    "do_karies",
    "do_periodontal",
    "do_ppok",
    "do_kadar_co",
    "do_lipid",
    "do_fibrosis",
    "do_hepatitis",
    "do_fungsi_ginjal_perempuan",
    "do_kerusakan_ginjal",
    "do_kanker_payudara",
    "do_hpv_dna",
    "do_inspekulo_iva",
    "do_jantung",
    "do_kanker_usus",
    "do_kanker_paru",
    "do_catin_perempuan",
    "do_hiv",
    "do_sifilis",
]
```

Secara domain, tahap ini mengisi form pemeriksaan tenaga kesehatan, seperti gizi, tekanan darah, gula darah, pemeriksaan penyakit menular, pemeriksaan laboratorium, dan skrining kanker yang membutuhkan input klinis atau hasil pemeriksaan.

## Pemisahan Berdasarkan Jenis Kelamin

Pemisahan daftar method laki-laki dan perempuan diperlukan karena sebagian form bersifat spesifik jenis kelamin.

Contoh form spesifik perempuan:

- `do_demografi_dewasa_perempuan`
- `do_fungsi_ginjal_perempuan`
- `do_kanker_payudara`
- `do_hpv_dna`
- `do_inspekulo_iva`
- `do_catin_perempuan`

Contoh form spesifik laki-laki:

- `do_gizi_laki`
- `do_fungsi_ginjal`

Jenis kelamin tidak diambil dari Excel, tetapi dibaca dari UI CKG setelah pasien berhasil dibuka. Hal ini membuat pemilihan alur skrining mengikuti data pasien yang tampil di sistem.

## Executor Skrining

`run_screening_steps()` adalah executor generik untuk menjalankan daftar method skrining. Fungsi ini menerima:

- Instance `ScreeningMandiri` atau `ScreeningNakes`.
- Daftar nama method yang harus dijalankan.
- Data baris Excel.
- Nomor baris Excel.
- Object `page` Playwright.

Untuk setiap nama method, executor melakukan langkah berikut:

1. Mengambil method dari instance skrining dengan `getattr()`.
2. Jika method tidak ada, proses method tersebut dilewati.
3. Mengecek ketersediaan form UI dengan `is_screening_form_available()`.
4. Menjalankan method jika form tersedia.
5. Jika terjadi `PlaywrightTimeoutError`, form aktif ditutup dan proses lanjut ke method berikutnya.

Pola ini membuat perubahan atau ketidakhadiran sebagian form di UI CKG tidak langsung menghentikan seluruh antrean pasien.

## Deteksi Form UI

`is_screening_form_available()` menggunakan `get_screening_form_id()` untuk membaca source method dan mencari pola ID form `rowfrm...`.

Contoh:

```python
self.page.locator('[id="rowfrm000006"]').click()
```

Dari source method tersebut, helper mengambil `rowfrm000006`, lalu menunggu elemen dengan ID tersebut tampil di UI. Jika elemen tidak muncul dalam batas `CKG_SCREENING_UI_TIMEOUT_MS`, method skrining dianggap tidak tersedia dan dilewati.

## Sumber Data

Data input berasal dari `dataset/dewasa.xlsx` melalui `ExcelStatusWorkbook`. Nilai sel diformat dengan `format_cell_value` sebelum dipakai untuk mengisi atau memilih opsi di UI.

Kolom yang dibutuhkan bergantung pada method yang dijalankan oleh `ScreeningMandiri` dan `ScreeningNakes`. Karena skrining mandiri dan nakes memakai data baris Excel yang sama, workbook harus memuat semua kolom yang dibaca oleh kedua helper tersebut.

## Konfigurasi Terkait

Konfigurasi dibaca dari `.env`:

- `CKG_USERNAME`: username untuk login CKG.
- `CKG_PASSWORD`: password untuk login CKG.
- `CKG_SCREENING_UI_TIMEOUT_MS`: timeout saat menunggu form skrining tampil. Default `5000`.
- `CKG_DEBUG_RAISE_ERRORS`: jika bernilai `1`, exception akan dilempar ulang untuk debugging.

## Batasan Teknis

- Script bergantung pada struktur UI CKG, termasuk teks, ID form `rowfrm...`, dan selector Playwright.
- Jika nama form, ID form, atau layout UI berubah, method terkait dapat dilewati atau gagal.
- Script hanya memproses pasien yang badge kategorinya `Dewasa`.
- Status `SUCCESS` ditulis setelah skrining mandiri dan skrining nakes untuk pasien tersebut selesai dijalankan tanpa exception.
