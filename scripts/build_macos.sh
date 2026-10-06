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

# create a new folder for dist
mkdir "dist/$VERSION"

rm -rf "dist/$VERSION/dataset"
cp -R dataset "dist/$VERSION/dataset"
cp .env.example "dist/$VERSION/.env.example"
cp "scripts/Jalankan CKG Helper.command" "dist/$VERSION/Jalankan CKG Helper.command"
chmod +x "dist/$VERSION/Jalankan CKG Helper.command"
mv "dist/ckg-helper" "dist/$VERSION/ckg-helper"


# Create release zip + checksum for auto-update
ZIP_NAME="ckg-helper-v$VERSION-macos.zip"
ZIP_PATH="dist/$ZIP_NAME"
rm -f "$ZIP_PATH"
zip -r "$ZIP_PATH" "dist/$VERSION"
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
