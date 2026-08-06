@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #93
echo d0=6a6602e187052930e014409322d3e13057  band_pos=66.25%  stages=1
echo Range 6a6602e187052930e01440932253e13057:6a6602e187052930e01440932353e13056  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 6a6602e187052930e01440932253e13057:6a6602e187052930e01440932353e13056 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
