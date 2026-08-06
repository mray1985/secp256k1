@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #98
echo d0=6f9516de685ecfc7e5840847e3894ca072  band_pos=74.35%  stages=4
echo Range 6f9516de685ecfc7e5840847e3094ca072:6f9516de685ecfc7e5840847e4094ca071  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 6f9516de685ecfc7e5840847e3094ca072:6f9516de685ecfc7e5840847e4094ca071 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
