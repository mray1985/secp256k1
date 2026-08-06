@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 216/255  eps [d8000000,d8ffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[3623878656,3640655871]  tile=216
echo Range e84818e1bf7f699aa6e28ef9edfb4820d8ffffff:e84818e1bf7f699aa6e28ef9edfb5820d8ffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb4820d8ffffff:e84818e1bf7f699aa6e28ef9edfb5820d8ffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
