@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x801  tz=2^143
echo stage=SE_pivot198.95_raw_ceil
echo span=2^143  m=2^72  suggested -k 36893488147419103232
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400800000000000000000000000000000000000:400ffffffffffffffffffffffffffffffffffff -k 36893488147419103232 -t %THREADS% -s %STATS% -q
pause
