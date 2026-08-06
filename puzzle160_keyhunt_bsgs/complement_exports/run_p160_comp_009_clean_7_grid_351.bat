@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_7_grid_351
echo Source: g_prune_clean
echo Center d=772928382695806375533223926084004801388554832890
echo m partner=149809596632301856617234119071
echo Range 87634eb09f710d66be5e27699f651f79c9283bfa:87634eb09f710d66be5e27699f65214b72725bfa  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 87634eb09f710d66be5e27699f651f79c9283bfa:87634eb09f710d66be5e27699f65214b72725bfa -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
