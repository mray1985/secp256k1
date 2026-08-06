@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_1_eps_398572964860
echo Source: g_prune_clean
echo Center d=847247326175473436694258913993724266786719010809
echo m partner=136668580307014731078624608256
echo Range 9467e2522be0621432c46b96cf8b5d68c1defff9:9467e2522be0621432c46b96cf8b5f3a6b291ff9  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 9467e2522be0621432c46b96cf8b5d68c1defff9:9467e2522be0621432c46b96cf8b5f3a6b291ff9 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
