@echo off
setlocal
call "%~dp0paths.bat"

if not exist "%KEYHUNT%" (
  echo ERROR: keyhunt not found: %KEYHUNT%
  pause
  exit /b 1
)

set "FULL=%~dp0h160_lane_exports\run_p160_h160_lane_FULL.bat"
if not exist "%FULL%" (
  echo Generating h160 lane exports...
  python "%~dp0make_h160_lane_exports.py"
)

if not exist "%FULL%" (
  echo ERROR: could not create %FULL%
  pause
  exit /b 1
)

echo Running one-shot FULL h160 lane window...
call "%FULL%"
