@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_9_grid_173
echo Source: g_prune_clean
echo Center d=1015576093665565696247357715406948506896707457984
echo m partner=114016162806060607653653349741
echo Range b1e401ce55c8eac79007398b4bd21ecc0f1483c0:b1e401ce55c8eac79007398b4bd2209db85ea3c0  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r b1e401ce55c8eac79007398b4bd21ecc0f1483c0:b1e401ce55c8eac79007398b4bd2209db85ea3c0 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
