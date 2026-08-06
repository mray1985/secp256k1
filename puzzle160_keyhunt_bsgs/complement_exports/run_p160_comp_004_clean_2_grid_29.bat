@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_2_grid_29
echo Source: g_prune_clean
echo Center d=1271440886287870700141322231356802096315438623814
echo m partner=91071547632376016924537633619
echo Range deb5619416f5ab0ca0b7ad637b4ebc9d58ce6c46:deb5619416f5ab0ca0b7ad637b4ecc9d58ce6c46  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r deb5619416f5ab0ca0b7ad637b4ebc9d58ce6c46:deb5619416f5ab0ca0b7ad637b4ecc9d58ce6c46 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
