@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #63
echo d0=4d271e07f0b37900000000000000000000  band_pos=20.55%  stages=1
echo Range 4d271e07f0b378ffffffffffff80000000:4d271e07f0b3790000000000007fffffff  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 4d271e07f0b378ffffffffffff80000000:4d271e07f0b3790000000000007fffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
