@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x100001  tz=2^134
echo stage=SE_pivot198.95_minus8_floor
echo span=2^134  m=2^67  suggested -k 1152921504606846976
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400004000000000000000000000000000000000:400007fffffffffffffffffffffffffffffffff -k 1152921504606846976 -t %THREADS% -s %STATS% -q
pause
