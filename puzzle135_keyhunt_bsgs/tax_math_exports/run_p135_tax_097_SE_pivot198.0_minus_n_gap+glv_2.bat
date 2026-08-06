@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #97
echo d0=6d0c602579efaed31e6e9839aa8710b9c8  band_pos=70.39%  stages=1
echo Range 6d0c602579efaed31e6e9839aa0710b9c8:6d0c602579efaed31e6e9839ab0710b9c7  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 6d0c602579efaed31e6e9839aa0710b9c8:6d0c602579efaed31e6e9839ab0710b9c7 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
