@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_10_grid_134
echo Source: g_prune_clean
echo Center d=1090590236947681344265628455575702719569120294339
echo m partner=106173781237389772206576664326
echo Range bf07c1f07c1f07c1f07c1f36584efb8f857865c3:bf07c1f07c1f07c1f07c1f36584efd612ec285c3  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r bf07c1f07c1f07c1f07c1f36584efb8f857865c3:bf07c1f07c1f07c1f07c1f36584efd612ec285c3 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
