@echo off
setlocal
cd /d "%~dp0"

echo Puzzle 71 — FULL baby library on E:
echo   baby_h160.bin  ~858 GB  (2^35 x 25 bytes)
echo   baby_x.bin     ~144 GB  (2^35 x 36 bytes, EC-BSGS ready)
echo   Total          ~1 TB
echo.
echo Requires E: writable — run setup_e_drive_admin.bat first if needed.
echo.

if not exist E:\ (
  echo ERROR: E: not accessible. Run setup_e_drive_admin.bat as Administrator.
  pause
  exit /b 1
)

if not exist E:\puzzle71_bsgs\baby mkdir E:\puzzle71_bsgs\baby
if not exist E:\puzzle71_bsgs\logs mkdir E:\puzzle71_bsgs\logs

set LOG=E:\puzzle71_bsgs\logs\full_baby_build.log
echo Log: %LOG%
echo Building... resume with: python build_baby_h160.py --start-r N --x
echo.

python -u build_baby_h160.py --x 2>&1
pause
