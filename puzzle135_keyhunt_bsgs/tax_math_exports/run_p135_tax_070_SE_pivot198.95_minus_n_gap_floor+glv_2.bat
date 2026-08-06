@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #70
echo d0=5667f479e3eb5b3c7faefdb374b07b3c15  band_pos=35.01%  stages=4
echo Range 5667f479e3eb5b3c7faefdb374307b3c15:5667f479e3eb5b3c7faefdb375307b3c14  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 5667f479e3eb5b3c7faefdb374307b3c15:5667f479e3eb5b3c7faefdb375307b3c14 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
