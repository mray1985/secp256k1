@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo h160 lane export: tile 249/255  eps [f9000000,f9ffffff]
echo q_h=138614061598878480877088849141041944608  core_eps=[4177526784,4194303999]  tile=249
echo Range e84818e1bf7f699aa6e28ef9edfb4820f9ffffff:e84818e1bf7f699aa6e28ef9edfb5820f9ffffff  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e84818e1bf7f699aa6e28ef9edfb4820f9ffffff:e84818e1bf7f699aa6e28ef9edfb5820f9ffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
