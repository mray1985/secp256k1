@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_7_grid_105
echo Source: g_prune_clean
echo Center d=948265276395301558968277115953571102811253351958
echo m partner=122109384493634211033348665671
echo Range a619af84b582ff24d0e8e21ee422981e3d1fa616:a619af84b582ff24d0e8e21ee422a81e3d1fa616  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r a619af84b582ff24d0e8e21ee422981e3d1fa616:a619af84b582ff24d0e8e21ee422a81e3d1fa616 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
