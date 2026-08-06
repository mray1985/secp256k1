@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_1
echo Source: rem=3543400468629839517466946
echo Center d=772259785845615692117749924120901631176920806537
echo m partner=149939296800914180949636284416
echo Range 87455393126687aaecd8d14994eb82ce58283489:87455393126687aaecd8d14994eb92ce58283489  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 87455393126687aaecd8d14994eb82ce58283489:87455393126687aaecd8d14994eb92ce58283489 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
