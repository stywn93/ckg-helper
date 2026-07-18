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

if (Test-Path "dist\dataset") {
  Remove-Item "dist\dataset" -Recurse -Force
}
Copy-Item "dataset" "dist\dataset" -Recurse
Copy-Item ".env.example" "dist\.env.example"
Copy-Item "scripts\Jalankan CKG Helper.bat" "dist\Jalankan CKG Helper.bat"

if (Test-Path "dist\kamus") {
  Remove-Item "dist\kamus" -Recurse -Force
}
New-Item -ItemType Directory -Force -Path "dist\kamus"
Copy-Item "docs\skrining-nakes.pdf", "docs\skrining-mandiri.pdf" "dist\kamus\"

# Create release zip + checksum for auto-update
$ZipName = "ckg-helper-v$Version-windows.zip"
$ZipPath = "dist\$ZipName"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path "dist\ckg-helper.exe" -DestinationPath $ZipPath -Force
$Hash = (Get-FileHash $ZipPath -Algorithm SHA256).Hash.ToLower()
Set-Content -Path "$ZipPath.sha256" -Value "$Hash  $ZipName" -Encoding ASCII

Write-Host ""
Write-Host "Build selesai:"
Write-Host "  dist\ckg-helper.exe"
Write-Host "  dist\$ZipName"
Write-Host "  dist\$ZipName.sha256"
Write-Host "  dist\Jalankan CKG Helper.bat"
Write-Host "  dist\dataset\"
Write-Host "  dist\kamus\"
Write-Host ""
Write-Host "Jalankan dengan double-click:"
Write-Host "  dist\Jalankan CKG Helper.bat"
Write-Host ""
Write-Host "Atau dari Command Prompt atau PowerShell:"
Write-Host "  cd dist"
Write-Host "  .\ckg-helper.exe"
