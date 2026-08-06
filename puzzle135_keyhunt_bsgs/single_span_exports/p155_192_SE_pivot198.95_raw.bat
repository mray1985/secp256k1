@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x10014e6b8feddc2a7  tz=2^90
echo stage=SE_pivot198.95_raw
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400539ae3fb770a9c0000000000000000000000:400539ae3fb770a9fffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
