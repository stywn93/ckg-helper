#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

# Read version from auto_update.py
VERSION="$(python3 -c "exec(open('src/helpers/auto_update.py').read()); print(__version__)")"

"$PYTHON_BIN" -m PyInstaller \
  --clean \
  --onefile \
  --name ckg-helper \
  --collect-all playwright \
  --hidden-import zoneinfo \
  --hidden-import tzdata \
  --add-data "src:src" \
  ckg_helper.py

rm -rf dist/dataset
cp -R dataset dist/dataset
cp .env.example dist/.env.example
cp "scripts/Jalankan CKG Helper.command" "dist/Jalankan CKG Helper.command"
chmod +x "dist/Jalankan CKG Helper.command"

rm -rf dist/kamus
mkdir -p dist/kamus
cp docs/skrining-nakes.pdf docs/skrining-mandiri.pdf dist/kamus/

# Create release zip + checksum for auto-update
ZIP_NAME="ckg-helper-v$VERSION-macos.zip"
ZIP_PATH="dist/$ZIP_NAME"
rm -f "$ZIP_PATH"
zip -j "$ZIP_PATH" dist/ckg-helper
SHA_HASH="$(shasum -a 256 "$ZIP_PATH" | cut -d' ' -f1)"
echo "$SHA_HASH  $ZIP_NAME" > "$ZIP_PATH.sha256"

echo ""
echo "Build selesai:"
echo "  dist/ckg-helper"
echo "  dist/$ZIP_NAME"
echo "  dist/$ZIP_NAME.sha256"
echo "  dist/Jalankan CKG Helper.command"
echo "  dist/dataset/"
echo "  dist/kamus/"
echo ""
echo "Jalankan dengan double-click:"
echo "  dist/Jalankan CKG Helper.command"
echo ""
echo "Atau dari Terminal:"
echo "  cd dist"
echo "  ./ckg-helper"
