#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" -m PyInstaller \
  --clean \
  --onefile \
  --name ckg-helper \
  --collect-all playwright \
  --add-data "src:src" \
  ckg_helper.py

rm -rf dist/dataset
cp -R dataset dist/dataset
cp .env.example dist/.env.example
cp "scripts/Jalankan CKG Helper.command" "dist/Jalankan CKG Helper.command"
chmod +x "dist/Jalankan CKG Helper.command"

echo ""
echo "Build selesai:"
echo "  dist/ckg-helper"
echo "  dist/Jalankan CKG Helper.command"
echo "  dist/dataset/"
echo ""
echo "Jalankan dengan double-click:"
echo "  dist/Jalankan CKG Helper.command"
echo ""
echo "Atau dari Terminal:"
echo "  cd dist"
echo "  ./ckg-helper"
