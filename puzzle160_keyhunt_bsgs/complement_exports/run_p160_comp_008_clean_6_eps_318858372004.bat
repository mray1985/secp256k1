@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_6_eps_318858372004
echo Source: g_prune_clean
echo Center d=925001036339734900087934340252737030483401035542
echo m partner=125180496765182014198407757824
echo Range a2067b23ce281ddcae8f63e40c75930788b0cf16:a2067b23ce281ddcae8f63e40c75a30788b0cf16  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r a2067b23ce281ddcae8f63e40c75930788b0cf16:a2067b23ce281ddcae8f63e40c75a30788b0cf16 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
