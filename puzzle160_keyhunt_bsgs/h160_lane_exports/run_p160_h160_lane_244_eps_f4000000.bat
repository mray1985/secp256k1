@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 244/255  eps [f4000000,f4ffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[4093640704,4110417919]  tile=244
echo Range e84818e1bf7f699aa6e28ef9edfb4820f4ffffff:e84818e1bf7f699aa6e28ef9edfb5820f4ffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb4820f4ffffff:e84818e1bf7f699aa6e28ef9edfb5820f4ffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
