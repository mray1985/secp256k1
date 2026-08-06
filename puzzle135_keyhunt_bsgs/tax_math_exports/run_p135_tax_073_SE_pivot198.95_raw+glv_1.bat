@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #73
echo d0=5a64c7552d1758458ef6cea770d0f5524a  band_pos=41.24%  stages=1
echo Range 5a64c7552d1758458ef6cea77050f5524a:5a64c7552d1758458ef6cea77150f55249  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 5a64c7552d1758458ef6cea77050f5524a:5a64c7552d1758458ef6cea77150f55249 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
