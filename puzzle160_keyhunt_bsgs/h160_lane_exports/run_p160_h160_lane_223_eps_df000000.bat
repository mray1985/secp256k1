@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 223/255  eps [df000000,dfffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[3741319168,3758096383]  tile=223
echo Range e84818e1bf7f699aa6e28ef9edfb4820dfffffff:e84818e1bf7f699aa6e28ef9edfb5820dfffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb4820dfffffff:e84818e1bf7f699aa6e28ef9edfb5820dfffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
