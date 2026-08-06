@echo off
REM Scan mid-band 2^29 baby table for P71 target
setlocal
cd /d "%~dp0"
python -u scan_baby_h160.py --baby-dir C:\puzzle71_bsgs\baby --m 536870912 --prefix-len 1
exit /b %ERRORLEVEL%
