@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_6_eps_212114115920
echo Source: g_prune_clean
echo Center d=1054601304886752241697263831605029951669396806916
echo m partner=109797028223619031780164632576
echo Range b8b9f542a914e924756cc8ca757c8efd06879d04:b8b9f542a914e924756cc8ca757c9efd06879d04  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r b8b9f542a914e924756cc8ca757c8efd06879d04:b8b9f542a914e924756cc8ca757c9efd06879d04 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
