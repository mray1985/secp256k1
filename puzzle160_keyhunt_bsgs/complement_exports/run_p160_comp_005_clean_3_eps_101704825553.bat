@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_3_eps_101704825553
echo Source: g_prune_clean
echo Center d=1233334715077996490316868697175182990301652405716
echo m partner=93885372577057044786474647552
echo Range d808a42f9e3550cfe99f3dcdf1b756bb0a514dd4:d808a42f9e3550cfe99f3dcdf1b766bb0a514dd4  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r d808a42f9e3550cfe99f3dcdf1b756bb0a514dd4:d808a42f9e3550cfe99f3dcdf1b766bb0a514dd4 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
