@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 037/255  eps [25000000,25ffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[620756992,637534207]  tile=37
echo Range e84818e1bf7f699aa6e28ef9edfb482025ffffff:e84818e1bf7f699aa6e28ef9edfb582025ffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb482025ffffff:e84818e1bf7f699aa6e28ef9edfb582025ffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
