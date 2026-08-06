@echo off
setlocal
call "%~dp0paths.bat"
echo Stopping KeyHunt P160 BSGS...
taskkill /IM keyhunt.exe /F 2>nul
if errorlevel 1 (
  echo No keyhunt.exe process found.
) else (
  echo keyhunt.exe stopped.
)
echo.
echo RAM freed (~8 GB when full -k 512 run was active).
echo Disk: bloom still at %WORKDIR%\keyhunt_bsgs_4_2147483648.blm ^(~7.2 GB^)
echo   To free disk: run archive_p160_bloom.bat ^(move to archive folder^)
echo   Or after E: is NTFS: move archive to E:\puzzle71_bsgs\
pause
