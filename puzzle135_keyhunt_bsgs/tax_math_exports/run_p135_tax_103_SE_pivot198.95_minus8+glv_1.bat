@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #103
echo d0=735a64c7552d1758458ef6cea770d0f4c0  band_pos=80.24%  stages=1
echo Range 735a64c7552d1758458ef6cea6f0d0f4c0:735a64c7552d1758458ef6cea7f0d0f4bf  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 735a64c7552d1758458ef6cea6f0d0f4c0:735a64c7552d1758458ef6cea7f0d0f4bf -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
