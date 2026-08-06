@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #45
echo d0=4261be545b79a17b3f1f9610211f8e24de  band_pos=3.72%  stages=1
echo Range 4261be545b79a17b3f1f9610209f8e24de:4261be545b79a17b3f1f9610219f8e24dd  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 4261be545b79a17b3f1f9610209f8e24de:4261be545b79a17b3f1f9610219f8e24dd -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
