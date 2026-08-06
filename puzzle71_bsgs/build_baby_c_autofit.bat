@echo off
setlocal
cd /d "%~dp0"

set PUZZLE71_BSGS_ROOT=C:\puzzle71_bsgs
if not exist "%PUZZLE71_BSGS_ROOT%\baby" mkdir "%PUZZLE71_BSGS_ROOT%\baby"
if not exist "%PUZZLE71_BSGS_ROOT%\logs" mkdir "%PUZZLE71_BSGS_ROOT%\logs"
if not exist "%PUZZLE71_BSGS_ROOT%\giant" mkdir "%PUZZLE71_BSGS_ROOT%\giant"

set LOG=%PUZZLE71_BSGS_ROOT%\logs\baby_c_autofit.log
echo Puzzle 71 baby h160 — auto-fit to C: free space > "%LOG%"
echo Started %DATE% %TIME% >> "%LOG%"
echo. >> "%LOG%"

python -u build_baby_h160.py --out-dir "%PUZZLE71_BSGS_ROOT%\baby" --auto-fit >> "%LOG%" 2>&1
echo Exit %ERRORLEVEL% at %TIME% >> "%LOG%"
type "%LOG%"
