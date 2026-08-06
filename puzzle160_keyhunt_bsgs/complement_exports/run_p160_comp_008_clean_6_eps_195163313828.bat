@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_6_eps_195163313828
echo Source: g_prune_clean
echo Center d=1078598994488187249509890723374457725961961030325
echo m partner=107354160192093840610376548352
echo Range bcee0d3a0f044c48b815a9a973209a990e7c32b5:bcee0d3a0f044c48b815a9a973209c6ab7c652b5  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r bcee0d3a0f044c48b815a9a973209a990e7c32b5:bcee0d3a0f044c48b815a9a973209c6ab7c652b5 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
