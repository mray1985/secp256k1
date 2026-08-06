@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 108/255  eps [6c000000,6cffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[1811939328,1828716543]  tile=108
echo Range e84818e1bf7f699aa6e28ef9edfb48206cffffff:e84818e1bf7f699aa6e28ef9edfb58206cffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb48206cffffff:e84818e1bf7f699aa6e28ef9edfb58206cffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
