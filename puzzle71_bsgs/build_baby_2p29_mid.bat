@echo off
REM P71 baby hash160: M=2^29 window centered on mid-band (LO + 2^69)
setlocal
cd /d "%~dp0"

set ROOT=C:\puzzle71_bsgs
set M=536870912
for /f %%a in ('python -c "from p71_common import START_R_MID_2P29; print(START_R_MID_2P29)"') do set START_R=%%a

if not exist "%ROOT%\baby" mkdir "%ROOT%\baby"
if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

set LOG=%ROOT%\logs\baby_2p29_mid.log
if exist "%ROOT%\baby\baby_h160.bin" del /f "%ROOT%\baby\baby_h160.bin"
if exist "%ROOT%\baby\baby_meta.txt" del /f "%ROOT%\baby\baby_meta.txt"

echo Puzzle 71 baby h160  M=2^29 mid-band  start_r=%START_R%  (~13 GB) > "%LOG%"
echo Started %DATE% %TIME% >> "%LOG%"
echo d in [LO+%START_R%, LO+%START_R%+%M%) >> "%LOG%"
echo. >> "%LOG%"

python -u build_baby_h160.py --out-dir "%ROOT%\baby" --m %M% --start-r %START_R% >> "%LOG%" 2>&1
echo Exit %ERRORLEVEL% at %TIME% >> "%LOG%"
type "%LOG%"
