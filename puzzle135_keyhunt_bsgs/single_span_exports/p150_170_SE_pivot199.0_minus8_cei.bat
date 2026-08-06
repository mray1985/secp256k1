@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x2001  tz=2^136
echo stage=SE_pivot199.0_minus8_ceil
echo span=2^136  m=2^68  suggested -k 2305843009213693952
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20010000000000000000000000000000000000:2001ffffffffffffffffffffffffffffffffff -k 2305843009213693952 -t %THREADS% -s %STATS% -q
pause
