@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: small_rem_3
echo Source: rem=28147086641705317612011842
echo Center d=1205362177380791960866532459524416203030698514661
echo m partner=96064146868228586011661172736
echo Range d3224f3383d29e2dd2483d3210bfc065b4c9d8e5:d3224f3383d29e2dd2483d3210bfd065b4c9d8e5  span=17592186044417  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r d3224f3383d29e2dd2483d3210bfc065b4c9d8e5:d3224f3383d29e2dd2483d3210bfd065b4c9d8e5 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
