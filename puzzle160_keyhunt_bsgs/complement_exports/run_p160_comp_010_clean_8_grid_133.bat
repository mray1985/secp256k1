@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_8_grid_133
echo Source: g_prune_clean
echo Center d=1092659668137335388562147674651687649615326885388
echo m partner=105972694530500776425882390341
echo Range bf648dd82abf648dd82abf92f82d4f6c4665260c:bf648dd82abf648dd82abf92f82d513defaf460c  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r bf648dd82abf648dd82abf92f82d4f6c4665260c:bf648dd82abf648dd82abf92f82d513defaf460c -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
