@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #99
echo d0=70963fb9a2ba23fab56dddf38c8fba088c  band_pos=75.92%  stages=33
echo Range 70963fb9a2ba23fab56dddf38c0fba088c:70963fb9a2ba23fab56dddf38d0fba088b  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 70963fb9a2ba23fab56dddf38c0fba088c:70963fb9a2ba23fab56dddf38d0fba088b -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
