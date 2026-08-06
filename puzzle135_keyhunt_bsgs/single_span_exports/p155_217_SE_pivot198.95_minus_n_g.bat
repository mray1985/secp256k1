@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x10000000000000000000000000001  tz=2^42
echo stage=SE_pivot198.95_minus_n_gap_ceil
echo span=2^42  m=2^21  suggested -k 16384
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400000000000000000000000000040000000000:40000000000000000000000000007ffffffffff -k 16384 -t %THREADS% -s %STATS% -q
pause
