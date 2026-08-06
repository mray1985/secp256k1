@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_10_eps_274144896256
echo Source: g_prune_clean
echo Center d=975201273936353513185036750692854736292592702925
echo m partner=118736605798233773881392365568
echo Range aad1899b113449b00e9e0af154588f1667af55cd:aad1899b113449b00e9e0af154589f1667af55cd  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r aad1899b113449b00e9e0af154588f1667af55cd:aad1899b113449b00e9e0af154589f1667af55cd -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
