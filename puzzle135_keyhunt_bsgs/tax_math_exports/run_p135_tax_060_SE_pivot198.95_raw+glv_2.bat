@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #60
echo d0=4b367155a5d14f74e21262b11e5d8a452d  band_pos=17.52%  stages=1
echo Range 4b367155a5d14f74e21262b11ddd8a452d:4b367155a5d14f74e21262b11edd8a452c  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 4b367155a5d14f74e21262b11ddd8a452d:4b367155a5d14f74e21262b11edd8a452c -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
