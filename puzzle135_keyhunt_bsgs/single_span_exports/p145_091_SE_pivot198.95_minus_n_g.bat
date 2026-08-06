@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x10000000000000000000000000001  tz=2^32
echo stage=SE_pivot198.95_minus_n_gap_ceil
echo span=2^32  m=2^16  suggested -k 512
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1000000000000000000000000000100000000:10000000000000000000000000001ffffffff -k 512 -t %THREADS% -s %STATS% -q
pause
