@echo off
REM ============================================================
REM  Open E: for Puzzle 71 BSGS — MUST Run as Administrator
REM  Right-click this file -> Run as administrator
REM ============================================================
setlocal
echo.
echo === E: drive setup for puzzle71_bsgs ===
echo.

net session >nul 2>&1
if errorlevel 1 (
  echo ERROR: Not running as Administrator.
  echo Right-click this file and choose "Run as administrator"
  pause
  exit /b 1
)

echo [1] Disk / partition status
powershell -NoProfile -Command "Get-Disk -Number 1 | ft Number,FriendlyName,OperationalStatus,@{N='GB';E={[math]::Round($_.Size/1GB,1)}}; Get-Partition -DiskNumber 1 | ft DriveLetter,FileSystem,@{N='GB';E={[math]::Round($_.Size/1GB,1)}},OperationalStatus"
echo.

echo [2] Volume info
fsutil fsinfo volumeinfo E: 2>nul
if errorlevel 1 echo   fsutil: access denied or volume busy — may need chkdsk
echo.

echo [3] Online chkdsk scan (non-destructive)
chkdsk E: /scan
echo.

echo [4] Fix permissions on E:\
takeown /F E:\ /R /D Y >nul 2>&1
icacls E:\ /grant Administrators:(OI)(CI)F /T >nul 2>&1
icacls E:\ /grant "%USERNAME%":(OI)(CI)F /T >nul 2>&1
echo   takeown + icacls applied
echo.

echo [5] Write test
echo ok> E:\puzzle71_bsgs_write_test.txt 2>nul
if exist E:\puzzle71_bsgs_write_test.txt (
  echo   WRITE OK
  del E:\puzzle71_bsgs_write_test.txt
) else (
  echo   WRITE FAILED — try: chkdsk E: /F  then reboot if prompted
  echo   If exFAT: backup data, then format NTFS:
  echo     format E: /FS:NTFS /V:PUZZLE71 /Q
  pause
  exit /b 1
)

echo [6] Create BSGS folders
mkdir E:\puzzle71_bsgs\baby 2>nul
mkdir E:\puzzle71_bsgs\giant 2>nul
mkdir E:\puzzle71_bsgs\logs 2>nul
mkdir E:\puzzle71_bsgs\index 2>nul
echo   E:\puzzle71_bsgs ready
echo.

echo [7] Free space
powershell -NoProfile -Command "(Get-PSDrive E).Free/1GB"
echo.
echo SUCCESS. E: is writable. Run build_full_library.bat next.
pause
