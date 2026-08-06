@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #110
echo d0=7a89d0bde7139400000000000000000000  band_pos=91.47%  stages=2
echo Range 7a89d0bde71393ffffffffffff80000000:7a89d0bde713940000000000007fffffff  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 7a89d0bde71393ffffffffffff80000000:7a89d0bde713940000000000007fffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
