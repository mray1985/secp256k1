@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_4
echo Source: rem=1483091009954209319863337282
echo Center d=1043929740998388641016681927969289069840695905656
echo m partner=110919427514897218010691403776
echo Range b6db6db6ff58d0facd96047a68620204d9d94d78:b6db6db6ff58d0facd96047a68621204d9d94d78  span=17592186044417  (KeyHunt min span 100000000000)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r b6db6db6ff58d0facd96047a68620204d9d94d78:b6db6db6ff58d0facd96047a68621204d9d94d78 -k %K_FACTOR% -t %THREADS% -s %STATS% -S -q
pause
