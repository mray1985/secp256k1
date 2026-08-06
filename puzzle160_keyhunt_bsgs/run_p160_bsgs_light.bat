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
echo Puzzle 160 BSGS — LIGHT profile ^(priority: P71 / E: disk work^)
echo   K (-k) : %K_FACTOR_LIGHT%  ^(~2 GB bloom class, not 512^)
echo   threads: %THREADS_LIGHT%
echo   NOTE: uses separate bloom keyhunt_bsgs_* for k=128 — will build on first -S if missing.
echo   For narrow complement windows only; not full 2^159 band.
echo.
echo Press Ctrl+C to stop.
echo.

"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -b 160 -k %K_FACTOR_LIGHT% -t %THREADS_LIGHT% -s %STATS% -S -q
pause
