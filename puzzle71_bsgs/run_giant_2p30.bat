@echo off
REM Giant shard for M=2^30: baby scan (j=0) then live giant scroll
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_giant_2p30.bat J_INDEX
  exit /b 1
)
if "%~1"=="0" (
  python -u scan_baby_h160.py --baby-dir C:\puzzle71_bsgs\baby --m 1073741824 --prefix-len 1 --hit-path C:\puzzle71_bsgs\giant\HIT.txt
  if errorlevel 2 exit /b 2
  if not errorlevel 1 exit /b 0
)
python -u run_giant_shard.py --j %1 --m 1073741824 --work-dir C:\puzzle71_bsgs\giant --baby-dir C:\puzzle71_bsgs\baby --skip-baby-scan
