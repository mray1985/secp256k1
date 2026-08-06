@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #59
echo d0=4a883b9548b9e000000000000000479b95  band_pos=16.46%  stages=1
echo Range 4a883b9548b9dfffffffffffff80479b95:4a883b9548b9e000000000000080479b94  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 4a883b9548b9dfffffffffffff80479b95:4a883b9548b9e000000000000080479b94 -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
