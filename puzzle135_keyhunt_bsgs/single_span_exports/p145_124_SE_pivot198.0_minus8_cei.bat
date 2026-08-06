@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x801  tz=2^133
echo stage=SE_pivot198.0_minus8_ceil
echo span=2^133  m=2^67  suggested -k 1152921504606846976
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1002000000000000000000000000000000000:1003fffffffffffffffffffffffffffffffff -k 1152921504606846976 -t %THREADS% -s %STATS% -q
pause
