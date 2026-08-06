@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x10001  tz=2^133
echo stage=SE_pivot198.0_minus8_floor
echo span=2^133  m=2^67  suggested -k 1152921504606846976
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20002000000000000000000000000000000000:20003fffffffffffffffffffffffffffffffff -k 1152921504606846976 -t %THREADS% -s %STATS% -q
pause
