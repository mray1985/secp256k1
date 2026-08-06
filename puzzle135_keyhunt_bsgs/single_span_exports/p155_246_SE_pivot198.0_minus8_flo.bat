@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x400001  tz=2^132
echo stage=SE_pivot198.0_minus8_floor
echo span=2^132  m=2^66  suggested -k 576460752303423488
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400001000000000000000000000000000000000:400001fffffffffffffffffffffffffffffffff -k 576460752303423488 -t %THREADS% -s %STATS% -q
pause
