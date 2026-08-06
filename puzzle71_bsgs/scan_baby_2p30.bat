@echo off
REM Scan precomputed M=2^30 baby table for P71 target (j=0 lane only)
setlocal
cd /d "%~dp0"
python -u scan_baby_h160.py --baby-dir C:\puzzle71_bsgs\baby --m 1073741824 --prefix-len 1
exit /b %ERRORLEVEL%
