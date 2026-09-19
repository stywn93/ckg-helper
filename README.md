# CKG No Worry

<p align="center">
  <strong>Otomasi untuk membantu proses entri data CKG (Cek Kesehatan Gratis).</strong>
</p>

<p align="center">
  Aplikasi otomasi berbasis python dan playwright yang dapat membantu entri data Cek Kesehatan Gratis dengan lebih mudah dan cepat.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v0.4.0-orange" alt="Version">
  <img src="https://img.shields.io/badge/Python-Backend-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/MacOS-Supported-Yes?logo=apple&logoColor=white" alt="macOS">
  <img src="https://img.shields.io/badge/Windows-Supported-Yes?logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/Private-Yes-success" alt="private">
  <img src="https://img.shields.io/badge/Free-Yes-success" alt="free">
</p>

---

## ⚠️ Early Beta Tester

Beta tester (uji coba) untuk CKG Sekolah dapat diakses pada versi 0.4.0 yang dapat [diunduh di sini.](https://github.com/stywn93/ckg-helper/releases/tag/v0.4.0)

---
## ✅ Stable Release

Versi stabil adalah 0.3.9 yang dapat [diunduh di sini.](https://github.com/stywn93/ckg-helper/releases#release-v0.3.9)

---

## 🖥️ Preview

<p align="center">
  <img src="./Screenshot 2026-09-16 at 20.03.43.png" alt="CKG Helper Dashboard" width="100%">
</p>

> **Simplify knowledge work without losing structure.**

---

## ✨ Features

CKG No Worry saat ini mampu menjalankan :

- CKG Umum - Pendaftaran Baru
- CKG Umum - Konfirmasi Kehadiran
- CKG Umum - Pelayanan Anak
- CKG Umum - Pelayanan Remaja
- CKG Umum - Pelayanan Dewasa
- CKG Umum - Pelayanan Lansia
- CKG Sekolah - Pendaftaran Baru
- CKG Sekolah - Konfirmasi Kehadiran
---

# 🏗️ Susunan Folder
Setelah mengunduh aplikasi, pastikan dataset diletakkan pada folder `dataset/`.
Aplikasi mendukung 2 metode dataset:
1. **File Gabungan (Direkomendasikan)**: Satu file `dataset/ckg_data.xlsx` yang berisi sheet terpisah untuk setiap layanan (`anak`, `dewasa`, `remaja`, `lansia`, `pendaftaran_umum`, `konfirm_kehadiran`, `pendaftaran_sekolah`, `konfirm_kehadiran_sekolah`, `pelayanan_sekolah`).
2. **File Terpisah**: File `.xlsx` individual seperti sebelumnya.

```text
CKG Helper
│
├── ckg-helper.exe
│
├── dataset/
│   ├── ckg_data.xlsx                  # (Rekomendasi) 1 file berisi seluruh sheet
│   │
│   # ATAU file terpisah:
│   ├── anak.xlsx
│   ├── dewasa.xlsx
│   ├── konfirm_kehadiran_sekolah.xlsx
│   ├── konfirm_kehadiran.xlsx
│   ├── lansia.xlsx
│   ├── pelayanan_sekolah.xlsx
│   ├── pendaftaran_sekolah.xlsx
│   ├── pendaftaran_umum.xlsx
│   └── remaja.xlsx
```