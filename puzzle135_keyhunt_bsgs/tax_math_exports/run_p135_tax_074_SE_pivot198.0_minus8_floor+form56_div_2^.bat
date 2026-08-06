@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #74
echo d0=5c63061b50a13900000000000000000000  band_pos=44.35%  stages=1
echo Range 5c63061b50a138ffffffffffff80000000:5c63061b50a1390000000000007fffffff  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 5c63061b50a138ffffffffffff80000000:5c63061b50a1390000000000007fffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
