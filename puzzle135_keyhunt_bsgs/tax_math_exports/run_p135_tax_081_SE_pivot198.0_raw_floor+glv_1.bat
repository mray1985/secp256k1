@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #81
echo d0=61be545b79a17b3f1f9610211f8e253207  band_pos=52.72%  stages=1
echo Range 61be545b79a17b3f1f9610211f0e253207:61be545b79a17b3f1f961021200e253206  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 61be545b79a17b3f1f9610211f0e253207:61be545b79a17b3f1f961021200e253206 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
