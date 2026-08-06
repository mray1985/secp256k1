@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x40000000000000000000000000001  tz=2^45
echo stage=SE_pivot198.0_minus_n_gap_ceil
echo span=2^45  m=2^23  suggested -k 65536
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000000000000000000000000000200000000000:80000000000000000000000000003fffffffffff -k 65536 -t %THREADS% -s %STATS% -q
pause
