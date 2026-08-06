@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_0_grid_596
echo Source: g_prune_clean
echo Center d=1329323340540429755950362204455410006815829811444
echo m partner=87106037866033030487396501556
echo Range e8d8eb910dc0725d6336ef2f469a656a194260f4:e8d8eb910dc0725d6336ef2f469a756a194260f4  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r e8d8eb910dc0725d6336ef2f469a656a194260f4:e8d8eb910dc0725d6336ef2f469a756a194260f4 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
