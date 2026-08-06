@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #108
echo d0=7906ae92197a130381a7bf7b81c72b3556  band_pos=89.10%  stages=4
echo Range 7906ae92197a130381a7bf7b81472b3556:7906ae92197a130381a7bf7b82472b3555  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 7906ae92197a130381a7bf7b81472b3556:7906ae92197a130381a7bf7b82472b3555 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
