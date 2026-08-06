@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_3
echo Source: rem=1392261963606475112168440130
echo Center d=974334424939256195973707167520750974446872254803
echo m partner=118842243765055438114978267136
echo Range aaaaaaaad1c71c71d012f684bfaefb283db75953:aaaaaaaad1c71c71d012f684bfaf0b283db75953  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r aaaaaaaad1c71c71d012f684bfaefb283db75953:aaaaaaaad1c71c71d012f684bfaf0b283db75953 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
