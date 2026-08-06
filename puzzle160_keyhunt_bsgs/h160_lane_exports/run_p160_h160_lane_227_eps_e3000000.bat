@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 227/255  eps [e3000000,e3ffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[3808428032,3825205247]  tile=227
echo Range e84818e1bf7f699aa6e28ef9edfb4820e3ffffff:e84818e1bf7f699aa6e28ef9edfb5820e3ffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb4820e3ffffff:e84818e1bf7f699aa6e28ef9edfb5820e3ffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
