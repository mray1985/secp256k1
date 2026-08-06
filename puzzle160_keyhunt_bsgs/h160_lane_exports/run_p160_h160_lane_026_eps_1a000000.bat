@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 026/255  eps [1a000000,1affffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[436207616,452984831]  tile=26
echo Range e84818e1bf7f699aa6e28ef9edfb48201affffff:e84818e1bf7f699aa6e28ef9edfb58201affffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb48201affffff:e84818e1bf7f699aa6e28ef9edfb58201affffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
