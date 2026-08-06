@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_8_grid_813
echo Source: g_prune_clean
echo Center d=1286945910703897765787114285324611713202932228867
echo m partner=89974324697130021020896507621
echo Range e16ca6879d9dd79bcfb5fe42d18d029da1e12303:e16ca6879d9dd79bcfb5fe42d18d129da1e12303  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e16ca6879d9dd79bcfb5fe42d18d029da1e12303:e16ca6879d9dd79bcfb5fe42d18d129da1e12303 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
