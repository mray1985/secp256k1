@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_7_grid_4605
echo Source: g_prune_clean
echo Center d=826515785844082657959513829582870544006971609155
echo m partner=140096645727175127486481867061
echo Range 90c63fe8d01aaa47bc2d850a5ea73854eb5b5043:90c63fe8d01aaa47bc2d850a5ea74854eb5b5043  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 90c63fe8d01aaa47bc2d850a5ea73854eb5b5043:90c63fe8d01aaa47bc2d850a5ea74854eb5b5043 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
