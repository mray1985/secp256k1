@echo off
setlocal EnableDelayedExpansion
call "%~dp0paths.bat"

if not exist "%KEYHUNT%" (
  echo ERROR: keyhunt not found: %KEYHUNT%
  pause
  exit /b 1
)

set "BLOOM=%WORKDIR%\keyhunt_bsgs_4_2147483648.blm"
if not exist "%BLOOM%" (
  echo ERROR: bloom missing — run rebuild_bloom.bat first
  pause
  exit /b 1
)

for %%F in ("%BLOOM%") do if %%~zF LSS 7000000000 (
  echo ERROR: bloom looks truncated ^(%%~zF bytes^) — rerun rebuild_bloom.bat
  pause
  exit /b 1
)

cd /d "%WORKDIR%"
echo.
echo Complement queue — narrow d windows from complement_exports/
echo   Uses existing bloom ^(no -S^). Lower threads so full-band search can share CPU.
echo   Stop with Ctrl+C between windows.
echo.

set QUEUE_THREADS=2
set /a N=0
for %%B in ("%~dp0complement_exports\run_p160_comp_*.bat") do set /a N+=1
echo Found %N% complement bats. Running with -t %QUEUE_THREADS% ...
echo.

for %%B in ("%~dp0complement_exports\run_p160_comp_*.bat") do (
  echo.
  echo ===== %%~nxB =====
  for /f "usebackq tokens=1,* delims=:" %%L in (`findstr /i /c:"Range " "%%~fB"`) do echo %%L:%%M
  for /f "usebackq tokens=1,* delims=:" %%L in (`findstr /i /c:"Center d=" "%%~fB"`) do echo %%L:%%M
  for /f "usebackq tokens=2 delims=:" %%R in (`findstr /i /c:"-r " "%%~fB"`) do (
    set "RANGE=%%R"
    set "RANGE=!RANGE: =!"
    set "RANGE=!RANGE:"=!"
    "%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r !RANGE! -k %K_FACTOR% -t %QUEUE_THREADS% -s %STATS% -q
    if errorlevel 1 (
      echo [WARN] KeyHunt exited with error on %%~nxB
    )
  )
)

echo.
echo Complement queue finished.
pause
