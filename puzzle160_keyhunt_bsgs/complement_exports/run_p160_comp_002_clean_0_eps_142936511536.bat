@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: clean_0_eps_142936511536
echo Source: g_prune_clean
echo Center d=1159921934514992984131337128499141893588130653570
echo m partner=99827484757181720084745289728
echo Range cb2cb2cb8b078be6a10eada703aa5deee0b5d582:cb2cb2cb8b078be6a10eada703aa5fc089fff582  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r cb2cb2cb8b078be6a10eada703aa5deee0b5d582:cb2cb2cb8b078be6a10eada703aa5fc089fff582 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
