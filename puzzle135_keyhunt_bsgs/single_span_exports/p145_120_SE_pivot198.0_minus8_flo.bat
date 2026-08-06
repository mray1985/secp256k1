@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x1001  tz=2^132
echo stage=SE_pivot198.0_minus8_floor
echo span=2^132  m=2^66  suggested -k 576460752303423488
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1001000000000000000000000000000000000:1001fffffffffffffffffffffffffffffffff -k 576460752303423488 -t %THREADS% -s %STATS% -q
pause
