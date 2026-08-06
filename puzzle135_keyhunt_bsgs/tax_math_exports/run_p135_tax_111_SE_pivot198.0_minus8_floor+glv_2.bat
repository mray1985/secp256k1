@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #111
echo d0=7b3c8357490cbd0981c0d3dfbdc0e394fe  band_pos=92.56%  stages=2
echo Range 7b3c8357490cbd0981c0d3dfbd40e394fe:7b3c8357490cbd0981c0d3dfbe40e394fd  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 7b3c8357490cbd0981c0d3dfbd40e394fe:7b3c8357490cbd0981c0d3dfbe40e394fd -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
