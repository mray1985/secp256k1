@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_9_grid_1693
echo Source: g_prune_clean
echo Center d=1139617642013975815235187587466624157313351302882
echo m partner=101606086961486480327255979221
echo Range c79e38f2b64cee0cb8c3d4fee67669a6822c3ee2:c79e38f2b64cee0cb8c3d4fee67679a6822c3ee2  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r c79e38f2b64cee0cb8c3d4fee67669a6822c3ee2:c79e38f2b64cee0cb8c3d4fee67679a6822c3ee2 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
