@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 102/255  eps [66000000,66ffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[1711276032,1728053247]  tile=102
echo Range e84818e1bf7f699aa6e28ef9edfb482066ffffff:e84818e1bf7f699aa6e28ef9edfb582066ffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb482066ffffff:e84818e1bf7f699aa6e28ef9edfb582066ffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
