@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #68
echo d0=5404d782343e6400000000000000000000  band_pos=31.28%  stages=3
echo Range 5404d782343e63ffffffffffff80000000:5404d782343e640000000000007fffffff  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 5404d782343e63ffffffffffff80000000:5404d782343e640000000000007fffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
