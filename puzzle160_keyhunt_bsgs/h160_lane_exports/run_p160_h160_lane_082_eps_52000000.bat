@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 082/255  eps [52000000,52ffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[1375731712,1392508927]  tile=82
echo Range e84818e1bf7f699aa6e28ef9edfb482052ffffff:e84818e1bf7f699aa6e28ef9edfb582052ffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb482052ffffff:e84818e1bf7f699aa6e28ef9edfb582052ffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
