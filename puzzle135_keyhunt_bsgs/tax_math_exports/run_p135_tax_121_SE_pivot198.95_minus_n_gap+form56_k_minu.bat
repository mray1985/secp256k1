@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #121
echo d0=7fffffffffffffffffffffffffffffff5d  band_pos=100.00%  stages=9
echo Range 7fffffffffffffffffffffffff00000000:7fffffffffffffffffffffffffffffffff  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 7fffffffffffffffffffffffff00000000:7fffffffffffffffffffffffffffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
