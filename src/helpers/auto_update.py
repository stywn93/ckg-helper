import hashlib
import json
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

__version__ = "0.3.9"

GITHUB_API = "https://api.github.com/repos/stywn93/CKG-Helper/releases/latest"


def _get_platform_suffix() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "macos"
    return "linux"


def _parse_version(tag: str) -> tuple[int, int, int]:
    v = tag.lstrip("v")
    parts = v.split(".")
    return tuple(int(p) for p in parts[:3])


def check_for_update() -> dict | None:
    try:
        req = urllib.request.Request(
            GITHUB_API,
            headers={"User-Agent": "ckg-helper", "Accept": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    latest_tag = data.get("tag_name", "")
    if not latest_tag:
        return None

    try:
        latest_ver = _parse_version(latest_tag)
        current_ver = _parse_version(__version__)
    except (ValueError, IndexError):
        return None

    if latest_ver <= current_ver:
        return None

    suffix = _get_platform_suffix()
    asset_name = f"ckg-helper-{latest_tag}-{suffix}.zip"
    match = next(
        (a for a in data.get("assets", []) if a.get("name") == asset_name),
        None,
    )
    if not match:
        return None

    checksum_asset_name = f"{asset_name}.sha256"
    checksum_url = None
    for a in data.get("assets", []):
        if a.get("name") == checksum_asset_name:
            checksum_url = a.get("browser_download_url")
            break

    return {
        "version": latest_tag,
        "version_str": latest_tag.lstrip("v"),
        "download_url": match["browser_download_url"],
        "checksum_url": checksum_url,
        "changelog": data.get("body", ""),
    }


def _verify_checksum(file_path: Path, checksum_url: str | None) -> bool:
    if not checksum_url:
        return True
    try:
        req = urllib.request.Request(checksum_url, headers={"User-Agent": "ckg-helper"})
        resp = urllib.request.urlopen(req, timeout=10)
        line = resp.read().decode("utf-8").strip()
        expected = line.split()[0]
        actual = hashlib.sha256(file_path.read_bytes()).hexdigest()
        return actual == expected
    except Exception:
        return False


def download_update(info: dict, dest_dir: Path) -> Path | None:
    url = info["download_url"]
    zip_path = dest_dir / f"update-{info['version']}.zip"

    print(f"\nMengunduh update {info['version']}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ckg-helper"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(zip_path, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded * 100 // total
                        print(f"\r  {pct}% ({downloaded // 1024} KB / {total // 1024} KB)", end="", flush=True)
        print()
    except Exception as exc:
        print(f"  Gagal mendownload: {exc}")
        return None

    if not _verify_checksum(zip_path, info.get("checksum_url")):
        print("  Checksum tidak cocok. Update dibatalkan.")
        zip_path.unlink(missing_ok=True)
        return None

    print("  Ekstrak...")
    extract_dir = dest_dir / f"ckg-helper-{info['version']}"
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    zip_path.unlink()
    return extract_dir


def _write_updater_script(app_root: Path, extract_dir: Path, exe_name: str) -> Path | None:
    system = platform.system().lower()
    if system == "windows":
        return _write_updater_bat(app_root, extract_dir, exe_name)
    if system == "darwin":
        return _write_updater_command(app_root, extract_dir, exe_name)
    return None


def _write_updater_bat(app_root: Path, extract_dir: Path, exe_name: str) -> Path:
    bat_path = app_root / "__updater.bat"
    bat_path.write_text(
        f"""@echo off
cd /d "%~dp0"
echo Menunggu aplikasi ditutup...
:wait
tasklist /fi "imagename eq {exe_name}" 2>nul | find /i "{exe_name}" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto :wait
)
echo Memperbarui CKG Helper...
copy /y "{extract_dir}\\{exe_name}" "%~dp0{exe_name}" >nul 2>&1
rmdir /s /q "{extract_dir}" >nul 2>&1
echo Update selesai.
if exist "Jalankan CKG Helper.bat" (
    start "" "Jalankan CKG Helper.bat"
) else (
    start "" "{exe_name}"
)
del "%~f0"
""",
        encoding="utf-8",
    )
    return bat_path


def _write_updater_command(app_root: Path, extract_dir: Path, exe_name: str) -> Path:
    cmd_path = app_root / "__updater.command"
    cmd_path.write_text(
        f"""#!/bin/bash
cd "$(dirname "$0")"
echo "Menunggu aplikasi ditutup..."
while pgrep -f "{exe_name}" > /dev/null 2>&1; do
    sleep 1
done
echo "Memperbarui CKG Helper..."
cp "{extract_dir}/{exe_name}" "$(dirname "$0")/{exe_name}"
rm -rf "{extract_dir}"
echo "Update selesai."
if [ -x "./Jalankan CKG Helper.command" ]; then
    open "./Jalankan CKG Helper.command"
else
    open "./{exe_name}"
fi
rm -- "$0"
""",
        encoding="utf-8",
    )
    cmd_path.chmod(0o755)
    return cmd_path


def install_update(app_root: Path, info: dict) -> None:
    if not getattr(sys, "frozen", False):
        print("\nAuto-update hanya tersedia untuk aplikasi build. Jalankan dari source menggunakan git pull.")
        return

    temp_dir = app_root / "__update_temp__"
    temp_dir.mkdir(exist_ok=True)

    try:
        extract_dir = download_update(info, temp_dir)
        if extract_dir is None:
            return

        system = platform.system().lower()
        exe_name = "ckg-helper.exe" if system == "windows" else "ckg-helper"

        updater = _write_updater_script(app_root, extract_dir, exe_name)
        if updater is None:
            print(f"  Platform {platform.system()} tidak didukung untuk auto-update.")
            shutil.rmtree(extract_dir, ignore_errors=True)
            return

        print(f"\nUpdate siap. Menutup aplikasi...")
        subprocess.Popen([str(updater)], shell=True)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    sys.exit(0)
