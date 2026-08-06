@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_5_grid_364
echo Source: g_prune_clean
echo Center d=759672355024242413947561774338786776427230555225
echo m partner=152423723821858801766259680876
echo Range 8510e2f48463f7e4fb4592d0a781e2f084dd5c59:8510e2f48463f7e4fb4592d0a781e4c22e277c59  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 8510e2f48463f7e4fb4592d0a781e2f084dd5c59:8510e2f48463f7e4fb4592d0a781e4c22e277c59 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
