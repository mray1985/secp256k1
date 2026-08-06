@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #104
echo d0=742a32adcb9b97af52ecb303a1e236fbaf  band_pos=81.51%  stages=1
echo Range 742a32adcb9b97af52ecb303a16236fbaf:742a32adcb9b97af52ecb303a26236fbae  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 742a32adcb9b97af52ecb303a16236fbaf:742a32adcb9b97af52ecb303a26236fbae -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
