@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #83
echo d0=652cd9c55697453dd388498ac479762895  band_pos=58.09%  stages=1
echo Range 652cd9c55697453dd388498ac3f9762895:652cd9c55697453dd388498ac4f9762894  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 652cd9c55697453dd388498ac3f9762895:652cd9c55697453dd388498ac4f9762894 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
