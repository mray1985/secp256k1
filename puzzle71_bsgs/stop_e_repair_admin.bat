@echo off
REM Stop E: auto-repair loop — Run as Administrator
REM Close all Explorer windows on E: before running.
setlocal
net session >nul 2>&1
if errorlevel 1 (
  echo Run as Administrator: right-click this file -^> Run as administrator
  pause
  exit /b 1
)

echo === Stop repair / lock on E: ===
echo.

echo [1] Kill chkdsk if running
taskkill /F /IM chkdsk.exe 2>nul
taskkill /F /IM CHKDSK.EXE 2>nul
echo.

echo [2] Exclude E: from boot-time autochk (stops reschedule loop)
chkntfs /x E:
chkntfs E:
echo.

echo [3] Stop Windows Search (often hammers broken USB volumes)
net stop wsearch 2>nul
echo.

echo [4] Take partition OFFLINE then ONLINE (diskpart)
(
echo select volume E
echo offline disk
echo online disk
) | diskpart
echo.

echo [5] If still locked — unplug USB NOW, wait 10 sec, replug, press a key...
pause
echo.

echo [6] Write test
echo ok> E:\repair_stop_test.txt 2>nul
if exist E:\repair_stop_test.txt (
  echo SUCCESS: E: writable
  del E:\repair_stop_test.txt
) else (
  echo STILL BLOCKED — use format path in Disk Management or diskpart format below
  echo   diskmgmt.msc  -^> delete volume E -^> new NTFS volume
)

echo.
echo Done. Do NOT open E: Properties -^> Tools -^> Check ^(restarts repair^).
pause
