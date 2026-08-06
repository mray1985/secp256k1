@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x4000ef87d89980a95  tz=2^83
echo stage=SE_pivot198.95_minus8
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200077c3ec4cc054a800000000000000000000:200077c3ec4cc054afffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
