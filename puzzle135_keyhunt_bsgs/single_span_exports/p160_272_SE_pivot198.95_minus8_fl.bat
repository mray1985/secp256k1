@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x2000001  tz=2^134
echo stage=SE_pivot198.95_minus8_floor
echo span=2^134  m=2^67  suggested -k 1152921504606846976
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000004000000000000000000000000000000000:8000007fffffffffffffffffffffffffffffffff -k 1152921504606846976 -t %THREADS% -s %STATS% -q
pause
