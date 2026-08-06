@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_11_grid_188
echo Source: g_prune_clean
echo Center d=989401452076246992735827877436014821857480596998
echo m partner=117032463409395544364067459516
echo Range ad4e4ba80709ad4e4ba8073f78ddf0ebbcd5ce06:ad4e4ba80709ad4e4ba8073f78ddf2bd661fee06  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r ad4e4ba80709ad4e4ba8073f78ddf0ebbcd5ce06:ad4e4ba80709ad4e4ba8073f78ddf2bd661fee06 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
