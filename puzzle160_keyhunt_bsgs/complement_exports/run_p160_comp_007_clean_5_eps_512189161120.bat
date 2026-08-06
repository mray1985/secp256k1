@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_5_eps_512189161120
echo Source: g_prune_clean
echo Center d=756601369222018614304573452363805114892314017294
echo m partner=153042399799487983599250046976
echo Range 84872dc45cbae18988ca2d1839d892f4620cfe0e:84872dc45cbae18988ca2d1839d8a2f4620cfe0e  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 84872dc45cbae18988ca2d1839d892f4620cfe0e:84872dc45cbae18988ca2d1839d8a2f4620cfe0e -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
