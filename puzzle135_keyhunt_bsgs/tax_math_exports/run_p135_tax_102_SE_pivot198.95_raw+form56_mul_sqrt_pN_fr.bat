@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #102
echo d0=7255129cc2670800000000000000000000  band_pos=78.64%  stages=1
echo Range 7255129cc26707ffffffffffff80000000:7255129cc267080000000000007fffffff  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 7255129cc26707ffffffffffff80000000:7255129cc267080000000000007fffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
