@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo Complement export: D_BASE
echo Source: ladder_D_BASE
echo Center d=1461501637330902918203684832716283019650474630374
echo m partner=None
echo Range fffffffffffffffffffffffffffff00000000000:ffffffffffffffffffffffffffffffffffffffff  span=17592186044416  (KeyHunt min span 100000000000)
REM Bloom already built in WORKDIR — do not pass -S (saves ~30 min + 8 GB rewrite per window)
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r fffffffffffffffffffffffffffff00000000000:ffffffffffffffffffffffffffffffffffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
