@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set LOGDIR=C:\puzzle71_bsgs\logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set MANIFEST=%LOGDIR%\pruned_files.txt
echo Prune run %DATE% %TIME% > "%MANIFEST%"

echo [1] P160 bloom archive (~8 GB, rebuild via rebuild_bloom.bat)
if exist "C:\Users\mitch\Desktop\secp256k1\puzzle160_keyhunt_bsgs\bloom_archive" (
  rmdir /s /q "C:\Users\mitch\Desktop\secp256k1\puzzle160_keyhunt_bsgs\bloom_archive"
  echo removed bloom_archive>> "%MANIFEST%"
)

echo [2] __pycache__ under secp256k1
for /d /r "C:\Users\mitch\Desktop\secp256k1" %%D in (__pycache__) do @if exist "%%D" rmdir /s /q "%%D"

echo [3] One-off root .py scripts (keep core puzzle work)
powershell -NoProfile -Command ^
  "$keep=@('puzzle71_harvester.py','puzzle_da_sequence.py','puzzle71_da_draft.py','puzzle71_multiplier_area.py','puzzle160_complement_focus.py','puzzle160_epsilon_ladder.py','barcode160_window_search.py','hashkeys_rsz.py','genesis_calibration.py','decode_genesis_poetic.py','verify_new_candidates_P160.py');" ^
  "$root='C:\Users\mitch\Desktop\secp256k1';" ^
  "$log='%MANIFEST%';" ^
  "Get-ChildItem $root -Filter '*.py' -File | Where-Object { $keep -notcontains $_.Name } | ForEach-Object { Add-Content $log $_.FullName; Remove-Item $_.FullName -Force }"

echo [4] F: test baby folder
if exist "F:\puzzle71_bsgs" rmdir /s /q "F:\puzzle71_bsgs"

for /f %%a in ('powershell -NoProfile -Command "[math]::Round((Get-PSDrive C).Free/1GB,1)"') do set FREE=%%a
echo C: free ~!FREE! GB>> "%MANIFEST%"
echo Done prune. C: free ~!FREE! GB
