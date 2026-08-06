@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #71
echo d0=599fd1e78fad6cf1febbf6cdd2c1ecf19b  band_pos=40.04%  stages=2
echo Range 599fd1e78fad6cf1febbf6cdd241ecf19b:599fd1e78fad6cf1febbf6cdd341ecf19a  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 599fd1e78fad6cf1febbf6cdd241ecf19b:599fd1e78fad6cf1febbf6cdd341ecf19a -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
