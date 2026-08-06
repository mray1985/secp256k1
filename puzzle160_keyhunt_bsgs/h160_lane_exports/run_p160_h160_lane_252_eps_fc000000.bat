@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 252/255  eps [fc000000,fcffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[4227858432,4244635647]  tile=252
echo Range e84818e1bf7f699aa6e28ef9edfb4820fcffffff:e84818e1bf7f699aa6e28ef9edfb5820fcffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb4820fcffffff:e84818e1bf7f699aa6e28ef9edfb5820fcffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
