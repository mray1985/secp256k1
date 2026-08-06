@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #96
echo d0=6cf20d5d2432f42607034f7ef7038e55e1  band_pos=70.23%  stages=2
echo Range 6cf20d5d2432f42607034f7ef6838e55e1:6cf20d5d2432f42607034f7ef7838e55e0  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 6cf20d5d2432f42607034f7ef6838e55e1:6cf20d5d2432f42607034f7ef7838e55e0 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
