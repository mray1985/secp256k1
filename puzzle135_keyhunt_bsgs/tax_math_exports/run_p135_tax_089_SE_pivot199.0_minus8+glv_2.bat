@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #89
echo d0=682f573548d191a142b44d33f17875f969  band_pos=62.79%  stages=1
echo Range 682f573548d191a142b44d33f0f875f969:682f573548d191a142b44d33f1f875f968  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 682f573548d191a142b44d33f0f875f969:682f573548d191a142b44d33f1f875f968 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
