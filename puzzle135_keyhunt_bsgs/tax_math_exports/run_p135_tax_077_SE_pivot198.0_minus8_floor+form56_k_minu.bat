@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #77
echo d0=5fffffffffffffffffffffffffff70c8d6  band_pos=50.00%  stages=1
echo Range 5fffffffffffffffffffffffff7f70c8d6:600000000000000000000000007f70c8d5  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 5fffffffffffffffffffffffff7f70c8d6:600000000000000000000000007f70c8d5 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
