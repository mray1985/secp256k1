@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_4_eps_448967243200
echo Source: g_prune_clean
echo Center d=804496318000495969111222192288681434073166703218
echo m partner=143931161207930860925916020736
echo Range 8ceadcd0aad31f0548f191e9c3835ead9b72ea72:8ceadcd0aad31f0548f191e9c3836ead9b72ea72  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 8ceadcd0aad31f0548f191e9c3835ead9b72ea72:8ceadcd0aad31f0548f191e9c3836ead9b72ea72 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
