@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x1  tz=2^139
echo stage=SE_pivot198.95_raw_floor
echo span=2^139  m=2^70  suggested -k 9223372036854775808
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 80000000000000000000000000000000000:fffffffffffffffffffffffffffffffffff -k 9223372036854775808 -t %THREADS% -s %STATS% -q
pause
