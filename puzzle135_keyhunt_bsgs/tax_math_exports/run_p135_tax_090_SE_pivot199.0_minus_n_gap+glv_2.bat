@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #90
echo d0=6863012bcf7d7698f374c1cd543885d213  band_pos=63.10%  stages=1
echo Range 6863012bcf7d7698f374c1cd53b885d213:6863012bcf7d7698f374c1cd54b885d212  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 6863012bcf7d7698f374c1cd53b885d213:6863012bcf7d7698f374c1cd54b885d212 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
