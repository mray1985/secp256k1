@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #46
echo d0=437ca8b6f342f67e3f2c20423f1c4a64b2  band_pos=5.45%  stages=1
echo Range 437ca8b6f342f67e3f2c20423e9c4a64b2:437ca8b6f342f67e3f2c20423f9c4a64b1  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 437ca8b6f342f67e3f2c20423e9c4a64b2:437ca8b6f342f67e3f2c20423f9c4a64b1 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
