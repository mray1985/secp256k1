@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #87
echo d0=65f42a32adcb9b97af52ecb303a1e2367a  band_pos=59.30%  stages=2
echo Range 65f42a32adcb9b97af52ecb30321e2367a:65f42a32adcb9b97af52ecb30421e23679  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 65f42a32adcb9b97af52ecb30321e2367a:65f42a32adcb9b97af52ecb30421e23679 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
