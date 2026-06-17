#!/bin/bash
cd "$(dirname "$0")"
if [ -x "./ckg-helper" ]; then
    ./ckg-helper
else
    echo "File ckg-helper tidak ditemukan di folder ini."
    echo "Pastikan Anda menjalankan file ini dari folder dist setelah build."
    read -r -p "Tekan Enter untuk menutup..."
fi
