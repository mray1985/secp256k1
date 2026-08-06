@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #113
echo d0=7d0a8cab72e6e5ebd4bb2cc0e8788dbe72  band_pos=95.38%  stages=1
echo Range 7d0a8cab72e6e5ebd4bb2cc0e7f88dbe72:7d0a8cab72e6e5ebd4bb2cc0e8f88dbe71  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 7d0a8cab72e6e5ebd4bb2cc0e7f88dbe72:7d0a8cab72e6e5ebd4bb2cc0e8f88dbe71 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
