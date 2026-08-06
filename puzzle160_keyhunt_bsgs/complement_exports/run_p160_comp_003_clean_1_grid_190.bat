@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_1_grid_190
echo Source: g_prune_clean
echo Center d=1416597803066208294261462952928616894871008573643
echo m partner=81739565730432209489235199886
echo Range f82271433a9e4d7ed743e4a5aa52f16725b9f8cb:f82271433a9e4d7ed743e4a5aa53016725b9f8cb  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r f82271433a9e4d7ed743e4a5aa52f16725b9f8cb:f82271433a9e4d7ed743e4a5aa53016725b9f8cb -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
