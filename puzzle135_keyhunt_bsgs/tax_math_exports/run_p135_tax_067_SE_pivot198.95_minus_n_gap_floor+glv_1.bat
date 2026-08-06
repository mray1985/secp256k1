@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 tax-math anchor BSGS #67
echo d0=5330170c3829498700a20499169f09868f  band_pos=29.98%  stages=4
echo Range 5330170c3829498700a20499161f09868f:5330170c3829498700a20499171f09868e  span=100000000
echo NOTE: span=100000000 < KeyHunt default min 100000000000; use -n 0x100000000 or your 2^32 profile
REM Bloom already built in WORKDIR — do not pass -S
"%KEYHUNT%" -m bsgs -f "%PUBFILE%" -r 5330170c3829498700a20499161f09868f:5330170c3829498700a20499171f09868e -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
