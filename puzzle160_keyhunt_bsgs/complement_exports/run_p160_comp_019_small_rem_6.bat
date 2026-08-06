@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_6
echo Source: rem=40447374275972898556406786
echo Center d=1344007489131855184368347180563174938466359295472
echo m partner=86154348226222047453239817516
echo Range eb6b615357e63c2bacbc36e2e1497df01d51bdf0:eb6b615357e63c2bacbc36e2e1498df01d51bdf0  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r eb6b615357e63c2bacbc36e2e1497df01d51bdf0:eb6b615357e63c2bacbc36e2e1498df01d51bdf0 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
