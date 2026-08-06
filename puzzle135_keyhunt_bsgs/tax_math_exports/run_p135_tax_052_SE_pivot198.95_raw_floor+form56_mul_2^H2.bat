@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #52
echo d0=48256bf3e8eaec00000000000000000000  band_pos=12.73%  stages=17
echo Range 48256bf3e8eaebffffffffffff80000000:48256bf3e8eaec0000000000007fffffff  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 48256bf3e8eaebffffffffffff80000000:48256bf3e8eaec0000000000007fffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
