@echo off
REM Wipe USB Disk 1 (Generic Flash Disk ~937 GB) and create clean NTFS E:
REM Run as Administrator. Close Drecov first.
setlocal
net session >nul 2>&1
if errorlevel 1 (
  echo Run as Administrator: right-click -^> Run as administrator
  pause
  exit /b 1
)

echo.
echo === WIPE E: (Disk 1 only) and format NTFS ===
echo This ERASES the entire ~937 GB USB stick.
echo KeyHunt / harvest data on E: will be destroyed.
echo.
set /p OK=Type YES to continue: 
if /I not "%OK%"=="YES" exit /b 1

echo.
echo [1] Stop Drecov / chkdsk if running
taskkill /F /IM Drecov.exe 2>nul
taskkill /F /IM chkdsk.exe 2>nul
chkntfs /x E: 2>nul
echo.

echo [2] diskpart — clean Disk 1, new NTFS E:
(
echo select disk 1
echo clean
echo create partition primary
echo format fs=ntfs label=PUZZLE71 quick
echo assign letter=E
echo exit
) | diskpart
if errorlevel 1 (
  echo diskpart FAILED — use diskmgmt.msc manually on Disk 1
  pause
  exit /b 1
)

echo.
echo [3] BSGS folders
mkdir E:\puzzle71_bsgs\baby 2>nul
mkdir E:\puzzle71_bsgs\giant 2>nul
mkdir E:\puzzle71_bsgs\logs 2>nul
mkdir E:\puzzle71_bsgs\index 2>nul

echo [4] Write test
echo ok> E:\puzzle71_bsgs_write_test.txt
if not exist E:\puzzle71_bsgs_write_test.txt (
  echo WRITE FAILED
  pause
  exit /b 1
)
del E:\puzzle71_bsgs_write_test.txt

echo.
echo SUCCESS. E: is clean NTFS.
echo Next: cd puzzle71_bsgs ^& python preflight_e.py ^& build_full_library.bat
pause
