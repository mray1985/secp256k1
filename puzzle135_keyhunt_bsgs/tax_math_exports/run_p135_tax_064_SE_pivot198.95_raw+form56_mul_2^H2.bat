@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #64
echo d0=4e6475837d1f4400000000000000000000  band_pos=22.49%  stages=2
echo Range 4e6475837d1f43ffffffffffff80000000:4e6475837d1f440000000000007fffffff  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 4e6475837d1f43ffffffffffff80000000:4e6475837d1f440000000000007fffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
