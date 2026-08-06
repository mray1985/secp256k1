@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_2_grid_3652
echo Source: g_prune_clean
echo Center d=908173420501910853380975228592221857827746509290
echo m partner=127499975911343643714935757476
echo Range 9f13e7956ad917d51cb73e3a45b36906023871ea:9f13e7956ad917d51cb73e3a45b37906023871ea  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 9f13e7956ad917d51cb73e3a45b36906023871ea:9f13e7956ad917d51cb73e3a45b37906023871ea -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
