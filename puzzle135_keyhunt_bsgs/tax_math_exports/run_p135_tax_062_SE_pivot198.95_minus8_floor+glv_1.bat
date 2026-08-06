@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #62
echo d0=4c37ca8b6f342f67e3f2c20423f1c4a5ef  band_pos=19.09%  stages=11
echo Range 4c37ca8b6f342f67e3f2c2042371c4a5ef:4c37ca8b6f342f67e3f2c2042471c4a5ee  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 4c37ca8b6f342f67e3f2c2042371c4a5ef:4c37ca8b6f342f67e3f2c2042471c4a5ee -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
