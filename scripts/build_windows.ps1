$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$PythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }

# Read version from auto_update.py
$VersionLine = Select-String -Path "src\helpers\auto_update.py" -Pattern '__version__\s*=\s*"([^"]+)"'
$Version = $VersionLine.Matches.Groups[1].Value

& $PythonBin -m PyInstaller `
  --clean `
  --onefile `
  --name ckg-helper `
  --collect-all playwright `
  --hidden-import zoneinfo `
  --hidden-import tzdata `
  --add-data "src;src" `
  ckg_helper.py

# Create a versioned folder for the release
$ReleaseDir = Join-Path $RootDir "dist\$Version"
if (Test-Path $ReleaseDir) {
  Remove-Item $ReleaseDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null

Remove-Item "dist\dataset" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item "dataset" "$ReleaseDir\dataset" -Recurse
Copy-Item ".env.example" "$ReleaseDir\.env.example"
Copy-Item "scripts\Jalankan CKG Helper.bat" "$ReleaseDir\Jalankan CKG Helper.bat"

Remove-Item "dist\kamus" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "$ReleaseDir\kamus" | Out-Null
Copy-Item "docs\skrining-nakes.pdf", "docs\skrining-mandiri.pdf" "$ReleaseDir\kamus\"

Move-Item "dist\ckg-helper.exe" "$ReleaseDir\ckg-helper.exe" -Force

# Create release zip + checksum for auto-update
$ZipName = "ckg-helper-v$Version-windows.zip"
$ZipPath = Join-Path $RootDir "dist\$ZipName"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
$ReleaseItems = Get-ChildItem -LiteralPath $ReleaseDir -Force
Compress-Archive -Path $ReleaseItems.FullName -DestinationPath $ZipPath -Force
$Hash = (Get-FileHash $ZipPath -Algorithm SHA256).Hash.ToLower()
Set-Content -Path "$ZipPath.sha256" -Value "$Hash  $ZipName" -Encoding ASCII

Write-Host ""
Write-Host "Build selesai:"
Write-Host "  $ReleaseDir\ckg-helper.exe"
Write-Host "  dist\$ZipName"
Write-Host "  dist\$ZipName.sha256"
Write-Host "  $ReleaseDir\Jalankan CKG Helper.bat"
Write-Host "  $ReleaseDir\dataset\"
Write-Host "  $ReleaseDir\kamus\"
Write-Host ""
Write-Host "Jalankan dengan double-click:"
Write-Host "  $ReleaseDir\Jalankan CKG Helper.bat"
Write-Host ""
Write-Host "Atau dari Command Prompt atau PowerShell:"
Write-Host "  cd $ReleaseDir"
Write-Host "  .\ckg-helper.exe"
