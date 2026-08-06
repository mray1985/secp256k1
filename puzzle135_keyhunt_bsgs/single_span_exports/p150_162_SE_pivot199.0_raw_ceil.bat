@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x21  tz=2^144
echo stage=SE_pivot199.0_raw_ceil
echo span=2^144  m=2^72  suggested -k 36893488147419103232
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 21000000000000000000000000000000000000:21ffffffffffffffffffffffffffffffffffff -k 36893488147419103232 -t %THREADS% -s %STATS% -q
pause
