@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x40ef87d89980a95  tz=2^91
echo stage=SE_pivot198.95_raw
echo span=2^91  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2077c3ec4cc054a80000000000000000000000:2077c3ec4cc054afffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
