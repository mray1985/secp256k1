@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_0
echo Source: rem=959820974799365342642498
echo Center d=1433313145766074770806141041617981949713638322435
echo m partner=80786316360356715094201073664
echo Range fb0ffbfc84b30bc0fda44ade1b5d983b91597103:fb0ffbfc84b30bc0fda44ade1b5da83b91597103  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r fb0ffbfc84b30bc0fda44ade1b5d983b91597103:fb0ffbfc84b30bc0fda44ade1b5da83b91597103 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
