@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_1_eps_65970697656
echo Source: g_prune_clean
echo Center d=1304912176210686036080664784860464873330763707550
echo m partner=88735542014454201718688186368
echo Range e4924924a31f58d0fc0405f8896bb19407a9349e:e4924924a31f58d0fc0405f8896bc19407a9349e  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e4924924a31f58d0fc0405f8896bb19407a9349e:e4924924a31f58d0fc0405f8896bc19407a9349e -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
