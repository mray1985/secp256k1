@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_4_grid_151
echo Source: g_prune_clean
echo Center d=821829906209261351105840167247703900465788971264
echo m partner=140895443646501012730786921913
echo Range 8ff420a636e8ff420a636ea812b1d84c70716900:8ff420a636e8ff420a636ea812b1e84c70716900  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 8ff420a636e8ff420a636ea812b1d84c70716900:8ff420a636e8ff420a636ea812b1e84c70716900 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
