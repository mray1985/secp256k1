@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #95
echo d0=6ce4dfded3a675284c77e53f279a90e3c7  band_pos=70.15%  stages=33
echo Range 6ce4dfded3a675284c77e53f271a90e3c7:6ce4dfded3a675284c77e53f281a90e3c6  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 6ce4dfded3a675284c77e53f271a90e3c7:6ce4dfded3a675284c77e53f281a90e3c6 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
