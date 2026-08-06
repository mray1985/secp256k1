@echo off
setlocal
call "%~dp0paths.bat"

if not exist "%KEYHUNT%" (
  echo ERROR: keyhunt not found: %KEYHUNT%
  pause
  exit /b 1
)

cd /d "%WORKDIR%"
echo.
echo Rebuilding KeyHunt BSGS bloom + bP table (deleted files are recreated with -S)
echo   K factor : %K_FACTOR%  (~8 GB RAM class per AlbertoBSD docs)
echo   threads  : %THREADS%
echo   output   : %WORKDIR%\keyhunt_bsgs_*.blm  and  keyhunt_bsgs_*.tbl
echo.
echo Removing any stale/corrupt bloom files first...
del /q keyhunt_bsgs_*.blm keyhunt_bsgs_*.tbl 2>nul
echo.
echo This one-time build can take a while. Let it finish all 4 files (~7-8 GB on disk).
echo Do NOT Ctrl+C until KeyHunt is searching (or you see all blooms written).
echo.

"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -b 160 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
