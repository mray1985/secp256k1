@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #101
echo d0=720d5d2432f42607034f7ef7038e566b4f  band_pos=78.21%  stages=2
echo Range 720d5d2432f42607034f7ef7030e566b4f:720d5d2432f42607034f7ef7040e566b4e  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 720d5d2432f42607034f7ef7030e566b4f:720d5d2432f42607034f7ef7040e566b4e -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
