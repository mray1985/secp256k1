@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_5
echo Source: rem=34940177316908042123706611
echo Center d=1171311781543178512062158975163829804131433351107
echo m partner=98856761335365862673025558661
echo Range cd2b6fd3a394cb5240b1742a4dc8fdc20d4887c3:cd2b6fd3a394cb5240b1742a4dc90dc20d4887c3  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r cd2b6fd3a394cb5240b1742a4dc8fdc20d4887c3:cd2b6fd3a394cb5240b1742a4dc90dc20d4887c3 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
