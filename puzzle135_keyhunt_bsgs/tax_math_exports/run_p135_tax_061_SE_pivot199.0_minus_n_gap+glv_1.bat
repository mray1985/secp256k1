@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #61
echo d0=4bce7f6a184144b386459f1955e3bd1653  band_pos=18.45%  stages=2
echo Range 4bce7f6a184144b386459f195563bd1653:4bce7f6a184144b386459f195663bd1652  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 4bce7f6a184144b386459f195563bd1653:4bce7f6a184144b386459f195663bd1652 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
