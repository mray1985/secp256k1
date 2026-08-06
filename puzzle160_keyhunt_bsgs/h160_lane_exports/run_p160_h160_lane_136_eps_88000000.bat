@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 136/255  eps [88000000,88ffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[2281701376,2298478591]  tile=136
echo Range e84818e1bf7f699aa6e28ef9edfb482088ffffff:e84818e1bf7f699aa6e28ef9edfb582088ffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb482088ffffff:e84818e1bf7f699aa6e28ef9edfb582088ffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
