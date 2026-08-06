@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 120/255  eps [78000000,78ffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[2013265920,2030043135]  tile=120
echo Range e84818e1bf7f699aa6e28ef9edfb482078ffffff:e84818e1bf7f699aa6e28ef9edfb582078ffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb482078ffffff:e84818e1bf7f699aa6e28ef9edfb582078ffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
