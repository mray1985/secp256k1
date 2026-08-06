@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #88
echo d0=6682f573548d191a142b44d33f17875f1c  band_pos=60.17%  stages=1
echo Range 6682f573548d191a142b44d33e97875f1c:6682f573548d191a142b44d33f97875f1b  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 6682f573548d191a142b44d33e97875f1c:6682f573548d191a142b44d33f97875f1b -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
