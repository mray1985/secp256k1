@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_11_eps_163460726912
echo Source: g_prune_clean
echo Center d=1126542888683233323254665949792539221572272567387
echo m partner=102785335916203333027207577600
echo Range c553ee2403f18ef6913d1ffcd9c995880c08b45b:c553ee2403f18ef6913d1ffcd9c9a5880c08b45b  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r c553ee2403f18ef6913d1ffcd9c995880c08b45b:c553ee2403f18ef6913d1ffcd9c9a5880c08b45b -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
