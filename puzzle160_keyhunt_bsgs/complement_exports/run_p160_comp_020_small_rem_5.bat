@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_5
echo Source: rem=1488717422721168209229188006
echo Center d=841339221490193371310133108889543885389569932956
echo m partner=137628302924263308087754181697
echo Range 935ef49af7a4d7bd26bde94ddfa4dd95de9b3e9c:935ef49af7a4d7bd26bde94ddfa4ed95de9b3e9c  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 935ef49af7a4d7bd26bde94ddfa4dd95de9b3e9c:935ef49af7a4d7bd26bde94ddfa4ed95de9b3e9c -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
