@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #50
echo d0=458a7c945c985c0000000000000000479b  band_pos=8.66%  stages=1
echo Range 458a7c945c985bffffffffffff8000479b:458a7c945c985c0000000000008000479a  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 458a7c945c985bffffffffffff8000479b:458a7c945c985c0000000000008000479a -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
