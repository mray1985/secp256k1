@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_10_grid_115
echo Source: g_prune_clean
echo Center d=917577079748204421137588536173080447459122146339
echo m partner=126193310396431341837139590941
echo Range a0b9944c3856296c87dedc77008cad1521a2ec23:a0b9944c3856296c87dedc77008cbd1521a2ec23  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r a0b9944c3856296c87dedc77008cad1521a2ec23:a0b9944c3856296c87dedc77008cbd1521a2ec23 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
