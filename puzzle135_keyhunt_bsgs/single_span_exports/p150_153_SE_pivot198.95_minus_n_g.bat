@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x10000000000000000000000000001  tz=2^37
echo stage=SE_pivot198.95_minus_n_gap_ceil
echo span=2^37  m=2^19  suggested -k 4096
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20000000000000000000000000002000000000:20000000000000000000000000003fffffffff -k 4096 -t %THREADS% -s %STATS% -q
pause
