@echo off
setlocal
cd /d "%~dp0"

set ROOT=C:\puzzle71_bsgs
set M=1073741824

if not exist "%ROOT%\baby" mkdir "%ROOT%\baby"
if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"
if not exist "%ROOT%\giant" mkdir "%ROOT%\giant"

set LOG=%ROOT%\logs\baby_2p30.log
echo Puzzle 71 baby h160  M=2^30  (~25 GB) > "%LOG%"
echo Started %DATE% %TIME% >> "%LOG%"
echo. >> "%LOG%"

python -u build_baby_h160.py --out-dir "%ROOT%\baby" --m %M% >> "%LOG%" 2>&1
echo Exit %ERRORLEVEL% at %TIME% >> "%LOG%"
type "%LOG%"
