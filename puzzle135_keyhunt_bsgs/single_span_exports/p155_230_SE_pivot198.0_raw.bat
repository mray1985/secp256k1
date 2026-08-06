@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x2000b33619a93bdf9  tz=2^89
echo stage=SE_pivot198.0_raw
echo span=2^89  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4001666c335277bf20000000000000000000000:4001666c335277bf3ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
