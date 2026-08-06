@echo off
setlocal
call "%~dp0paths.bat"

if not exist "%KEYHUNT%" (
  echo ERROR: keyhunt not found: %KEYHUNT%
  pause
  exit /b 1
)
if not exist "%PUBFILE%" (
  echo ERROR: pubkey file not found: %PUBFILE%
  pause
  exit /b 1
)

cd /d "%WORKDIR%"
echo.
echo Puzzle 160 BSGS  (full 2^159..2^160-1 band)
echo   binary : %KEYHUNT%
echo   pubkey : %PUBFILE%
echo   K (-k) : %K_FACTOR%  (~8 GB bloom class; same -k reloads cached files)
echo   cwd    : %WORKDIR%  (keyhunt_bsgs_*.blm / *.tbl land here)
echo.
echo Missing or corrupt blooms? Run rebuild_bloom.bat first (do not skip on first run).
echo.

if exist "%WORKDIR%\keyhunt_bsgs_4_2147483648.blm" (
  for %%A in ("%WORKDIR%\keyhunt_bsgs_4_2147483648.blm") do if %%~zA LSS 7000000000 (
    echo WARNING: bloom file looks truncated ^(%%~zA bytes^). Run rebuild_bloom.bat
    pause
    exit /b 1
  )
) else (
  echo NOTE: no bloom cache yet — run rebuild_bloom.bat once, or wait for -S to build ^(~8 GB^).
)

echo.

"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -b 160 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
