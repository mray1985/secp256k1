@echo off
setlocal
echo Puzzle 71 baby table — E:\puzzle71_bsgs\baby
echo Full 2^35 table ~858 GB h160; build in chunks with --start-r / --limit
echo.
cd /d "%~dp0"
if not exist "E:\puzzle71_bsgs\baby" mkdir "E:\puzzle71_bsgs\baby"
if not exist "E:\puzzle71_bsgs\logs" mkdir "E:\puzzle71_bsgs\logs"
python -u build_baby_h160.py --limit 2000000 --x
pause
