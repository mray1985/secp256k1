@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #76
echo d0=5eae6a91a3234285689a67e2f0ebf3db8e  band_pos=47.94%  stages=2
echo Range 5eae6a91a3234285689a67e2f06bf3db8e:5eae6a91a3234285689a67e2f16bf3db8d  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 5eae6a91a3234285689a67e2f06bf3db8e:5eae6a91a3234285689a67e2f16bf3db8d -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
