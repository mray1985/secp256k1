@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 043/255  eps [2b000000,2bffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[721420288,738197503]  tile=43
echo Range e84818e1bf7f699aa6e28ef9edfb48202bffffff:e84818e1bf7f699aa6e28ef9edfb58202bffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb48202bffffff:e84818e1bf7f699aa6e28ef9edfb58202bffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
