@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_2_eps_24739011612
echo Source: g_prune_clean
echo Center d=1398566160156816134405689344491025883501366676290
echo m partner=82793429825538499947790336000
echo Range f4f9e02749f4b05bff8294264f91da9b80a7fb42:f4f9e02749f4b05bff8294264f91dc6d29f21b42  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r f4f9e02749f4b05bff8294264f91da9b80a7fb42:f4f9e02749f4b05bff8294264f91dc6d29f21b42 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
