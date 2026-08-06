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
echo h160 lane queue — 256 eps tiles ^(2^24 per tile^)
echo   Lane: d = band_lo + q_h*2^32 + eps,  eps in [0, 2^32)
echo   Uses existing bloom ^(no -S^). Stop with Ctrl+C between windows.
echo.

set QUEUE_THREADS=2
set "EXPORT=%~dp0h160_lane_exports"

if not exist "%EXPORT%" (
  echo ERROR: missing h160_lane_exports — run: python make_h160_lane_exports.py
  pause
  exit /b 1
)

set /a DONE=0
set /a TOTAL=0
for %%B in ("%EXPORT%\run_p160_h160_lane_*.bat") do (
  if /i not "%%~nxB"=="run_p160_h160_lane_FULL.bat" set /a TOTAL+=1
)
echo Found %TOTAL% lane tiles. Priority tile 153 ^(h160 eps^) runs first.
echo.

call :run_bat "%EXPORT%\run_p160_h160_lane_153_eps_99000000.bat"

for %%B in ("%EXPORT%\run_p160_h160_lane_*.bat") do (
  if /i not "%%~nxB"=="run_p160_h160_lane_FULL.bat" (
    if /i not "%%~nxB"=="run_p160_h160_lane_153_eps_99000000.bat" (
      call :run_bat "%%~fB"
    )
  )
)

echo.
echo h160 lane tile queue finished ^(%DONE%/%TOTAL% tiles^).
echo Optional: run_h160_lane_single.bat for the one-shot FULL window.
pause
exit /b 0

:run_bat
echo.
echo ===== %~nx1 =====
for /f "usebackq tokens=1,* delims=:" %%L in (`findstr /i /c:"Range " "%~1"`) do echo %%L:%%M
for /f "usebackq tokens=2 delims=:" %%R in (`findstr /i /c:"-r " "%~1"`) do (
  set "RANGE=%%R"
  set "RANGE=!RANGE: =!"
  set "RANGE=!RANGE:"=!"
  "%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r !RANGE! -k %K_FACTOR% -t %QUEUE_THREADS% -s %STATS% -q
  if errorlevel 1 (
    echo [WARN] KeyHunt exited with error on %~nx1
  ) else (
    set /a DONE+=1
  )
)
exit /b 0
