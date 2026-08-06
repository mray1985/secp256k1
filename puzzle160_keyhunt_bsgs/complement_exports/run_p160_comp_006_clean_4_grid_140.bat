@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_4_grid_140
echo Source: g_prune_clean
echo Center d=1078336414060628744891857349361351657922024090842
echo m partner=107380301478723746890742308236
echo Range bce246f3891bce246f3891ec783a2bc07d319cda:bce246f3891bce246f3891ec783a2d92267bbcda  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r bce246f3891bce246f3891ec783a2bc07d319cda:bce246f3891bce246f3891ec783a2d92267bbcda -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
