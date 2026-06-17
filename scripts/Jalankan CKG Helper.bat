@echo off
cd /d "%~dp0"
if exist "ckg-helper.exe" (
    ckg-helper.exe
) else (
    echo File ckg-helper.exe tidak ditemukan di folder ini.
    echo Pastikan Anda menjalankan file ini dari folder dist setelah build.
)
pause
