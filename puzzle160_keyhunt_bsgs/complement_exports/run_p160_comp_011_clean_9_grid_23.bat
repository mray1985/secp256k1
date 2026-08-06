@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_9_grid_23
echo Source: g_prune_clean
echo Center d=1306595933835000765583017776885395761702756458662
echo m partner=88621192090697738442263078457
echo Range e4ddc9bb937726ee4ddc9bc280b43335c734a0a6:e4ddc9bb937726ee4ddc9bc280b44335c734a0a6  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e4ddc9bb937726ee4ddc9bc280b43335c734a0a6:e4ddc9bb937726ee4ddc9bc280b44335c734a0a6 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
