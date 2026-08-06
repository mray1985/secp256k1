@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x80001  tz=2^140
echo stage=SE_pivot198.0_raw_floor
echo span=2^140  m=2^70  suggested -k 9223372036854775808
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000100000000000000000000000000000000000:80001fffffffffffffffffffffffffffffffffff -k 9223372036854775808 -t %THREADS% -s %STATS% -q
pause
