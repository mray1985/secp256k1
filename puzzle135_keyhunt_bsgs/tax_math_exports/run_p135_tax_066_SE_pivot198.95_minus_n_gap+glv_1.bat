@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #66
echo d0=518dae0997d2f3f976c76f16ceee7ac0f5  band_pos=27.43%  stages=1
echo Range 518dae0997d2f3f976c76f16ce6e7ac0f5:518dae0997d2f3f976c76f16cf6e7ac0f4  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 518dae0997d2f3f976c76f16ce6e7ac0f5:518dae0997d2f3f976c76f16cf6e7ac0f4 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
