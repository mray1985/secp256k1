@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 087/255  eps [57000000,57ffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[1459617792,1476395007]  tile=87
echo Range e84818e1bf7f699aa6e28ef9edfb482057ffffff:e84818e1bf7f699aa6e28ef9edfb582057ffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb482057ffffff:e84818e1bf7f699aa6e28ef9edfb582057ffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
