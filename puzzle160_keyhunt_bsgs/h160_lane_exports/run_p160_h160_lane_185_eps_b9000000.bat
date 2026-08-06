@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 185/255  eps [b9000000,b9ffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[3103784960,3120562175]  tile=185
echo Range e84818e1bf7f699aa6e28ef9edfb4820b9ffffff:e84818e1bf7f699aa6e28ef9edfb5820b9ffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb4820b9ffffff:e84818e1bf7f699aa6e28ef9edfb5820b9ffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
