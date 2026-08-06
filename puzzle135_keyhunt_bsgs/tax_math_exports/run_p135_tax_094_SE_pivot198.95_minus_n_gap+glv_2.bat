@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #94
echo d0=6b9c947d9a0b4301a24e243a4c44614f20  band_pos=68.14%  stages=1
echo Range 6b9c947d9a0b4301a24e243a4bc4614f20:6b9c947d9a0b4301a24e243a4cc4614f1f  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 6b9c947d9a0b4301a24e243a4bc4614f20:6b9c947d9a0b4301a24e243a4cc4614f1f -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
