@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_0
echo Source: rem=55445970684420145345127507
echo Center d=1037534495690767116706760044340318791479930021711
echo m partner=111603122323392658285322061921
echo Range b5bca7e62b5bca7e62b5bcda8f4f6405fe51574f:b5bca7e62b5bca7e62b5bcda8f4f65d7a79b774f  (+-1000000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r b5bca7e62b5bca7e62b5bcda8f4f6405fe51574f:b5bca7e62b5bca7e62b5bcda8f4f65d7a79b774f -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
