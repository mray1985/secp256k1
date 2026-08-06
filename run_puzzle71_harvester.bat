@echo off
setlocal
cd /d "%~dp0"
echo Puzzle 71 Harvester — hash160 target, P+=G scroll
echo   log: puzzle71_harvester.log
echo.
python -u puzzle71_harvester.py --radius 100000 --log puzzle71_harvester.log
pause
