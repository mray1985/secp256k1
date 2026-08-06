@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 141/255  eps [8d000000,8dffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[2365587456,2382364671]  tile=141
echo Range e84818e1bf7f699aa6e28ef9edfb48208dffffff:e84818e1bf7f699aa6e28ef9edfb58208dffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb48208dffffff:e84818e1bf7f699aa6e28ef9edfb58208dffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
