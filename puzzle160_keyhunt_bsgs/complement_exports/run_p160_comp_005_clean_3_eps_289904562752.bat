@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_3_eps_289904562752
echo Source: g_prune_clean
echo Center d=956897627281962697154265762317991308160272815451
echo m partner=121007813099317578373875630080
echo Range a79cc60bf686d5fa7343e4e285c045ff6c15d55b:a79cc60bf686d5fa7343e4e285c055ff6c15d55b  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r a79cc60bf686d5fa7343e4e285c045ff6c15d55b:a79cc60bf686d5fa7343e4e285c055ff6c15d55b -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
