@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #3
echo d0=400000000000000000000000000000479b  band_pos=0.00%  stages=2
echo Range 4000000000000000000000000000000000:40000000000000000000000000ffffffff  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 4000000000000000000000000000000000:40000000000000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
