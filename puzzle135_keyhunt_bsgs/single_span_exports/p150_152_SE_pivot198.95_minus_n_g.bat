@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x20000000000000000000000000001  tz=2^36
echo stage=SE_pivot198.95_minus_n_gap_floor
echo span=2^36  m=2^18  suggested -k 2048
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20000000000000000000000000001000000000:20000000000000000000000000001fffffffff -k 2048 -t %THREADS% -s %STATS% -q
pause
