@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_4
echo Source: rem=28572221834843074007023938
echo Center d=996025653554917077713473378695473340804626027395
echo m partner=116254123399374731761701355520
echo Range ae7755c291d82b50db71813bc4224cf23f2a9383:ae7755c291d82b50db71813bc4225cf23f2a9383  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r ae7755c291d82b50db71813bc4224cf23f2a9383:ae7755c291d82b50db71813bc4225cf23f2a9383 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
