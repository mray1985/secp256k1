@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #106
echo d0=767906ae92197a130381a7bf7b81c72a9f  band_pos=85.11%  stages=8
echo Range 767906ae92197a130381a7bf7b01c72a9f:767906ae92197a130381a7bf7c01c72a9e  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 767906ae92197a130381a7bf7b01c72a9f:767906ae92197a130381a7bf7c01c72a9e -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
