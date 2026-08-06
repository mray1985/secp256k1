@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_11_grid_123
echo Source: g_prune_clean
echo Center d=894420560385473710194053178810847370726914450771
echo m partner=129460451118669046480172331157
echo Range 9cab347dfb27922b9bdc779c852a3ec5d574e553:9cab347dfb27922b9bdc779c852a4ec5d574e553  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 9cab347dfb27922b9bdc779c852a3ec5d574e553:9cab347dfb27922b9bdc779c852a4ec5d574e553 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
