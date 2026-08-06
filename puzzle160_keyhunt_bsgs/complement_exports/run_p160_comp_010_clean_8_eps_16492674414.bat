@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_8_eps_16492674414
echo Source: g_prune_clean
echo Center d=1418933628483220218274646483915446787233869042953
echo m partner=81605007389311803624830009344
echo Range f88b2f392f3ab59b163a2f713dcddf28a53d9509:f88b2f392f3ab59b163a2f713dcdef28a53d9509  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r f88b2f392f3ab59b163a2f713dcddf28a53d9509:f88b2f392f3ab59b163a2f713dcdef28a53d9509 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
