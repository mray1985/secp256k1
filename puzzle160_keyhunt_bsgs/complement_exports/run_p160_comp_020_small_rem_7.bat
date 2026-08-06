@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_7
echo Source: rem=57351734427980142207593190
echo Center d=959921193749882981778751593175234318891876312673
echo m partner=120626661846042099579359706076
echo Range a8245ae3380c1e4bbd5962f594da5992276f6661:a8245ae3380c1e4bbd5962f594da6992276f6661  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r a8245ae3380c1e4bbd5962f594da5992276f6661:a8245ae3380c1e4bbd5962f594da6992276f6661 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
