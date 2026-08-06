@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #105
echo d0=749c781fc2cde400000000000000000000  band_pos=82.21%  stages=8
echo Range 749c781fc2cde3ffffffffffff80000000:749c781fc2cde40000000000007fffffff  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 749c781fc2cde3ffffffffffff80000000:749c781fc2cde40000000000007fffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
