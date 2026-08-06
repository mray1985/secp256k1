@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_3_eps_206158430100
echo Source: g_prune_clean
echo Center d=1062910281847063674531241946361519025185136220305
echo m partner=108938723441549023878930497536
echo Range ba2e8ba35af9a7243da4d51c0e8ddef319258891:ba2e8ba35af9a7243da4d51c0e8de0c4c26fa891  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r ba2e8ba35af9a7243da4d51c0e8ddef319258891:ba2e8ba35af9a7243da4d51c0e8de0c4c26fa891 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
