@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_5_eps_285873023176
echo Source: g_prune_clean
echo Center d=961514235138773970676289037697844315592281243292
echo m partner=120426807015087082135835639808
echo Range a86bca1b1a23750229efeb1959dd074a99a33e9c:a86bca1b1a23750229efeb1959dd174a99a33e9c  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r a86bca1b1a23750229efeb1959dd074a99a33e9c:a86bca1b1a23750229efeb1959dd174a99a33e9c -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
