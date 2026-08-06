@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x201  tz=2^135
echo stage=SE_pivot198.95_minus8_ceil
echo span=2^135  m=2^68  suggested -k 2305843009213693952
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1008000000000000000000000000000000000:100ffffffffffffffffffffffffffffffffff -k 2305843009213693952 -t %THREADS% -s %STATS% -q
pause
