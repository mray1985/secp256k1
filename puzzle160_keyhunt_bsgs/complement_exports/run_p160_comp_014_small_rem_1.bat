@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_1
echo Source: rem=1244951581129678273891478660
echo Center d=1094715512132027668461447326775964490642157063458
echo m partner=105773680882445687818184964591
echo Range bfc0bdc6abfc0bdc6abfc0d032c1a5212971cd22:bfc0bdc6abfc0bdc6abfc0d032c1b5212971cd22  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r bfc0bdc6abfc0bdc6abfc0d032c1a5212971cd22:bfc0bdc6abfc0bdc6abfc0d032c1b5212971cd22 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
