@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #69
echo d0=54cc05c30e0a5261c028812645a7c26152  band_pos=32.50%  stages=1
echo Range 54cc05c30e0a5261c02881264527c26152:54cc05c30e0a5261c02881264627c26151  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 54cc05c30e0a5261c02881264527c26152:54cc05c30e0a5261c02881264627c26151 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
