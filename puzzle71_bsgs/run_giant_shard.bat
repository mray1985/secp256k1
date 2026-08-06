@echo off
setlocal
set "J=%~1"
if "%J%"=="" set "J=0"
set "M=34359738368"
cd /d "%~dp0"
if not exist "E:\puzzle71_bsgs\giant" mkdir "E:\puzzle71_bsgs\giant"
echo Giant shard j=%J%  checkpoints on E:\puzzle71_bsgs\giant
python -u run_giant_shard.py --j %J% --m %M%
pause
