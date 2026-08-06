@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x20000000000000000000000000001  tz=2^46
echo stage=SE_pivot198.95_minus_n_gap_floor
echo span=2^46  m=2^23  suggested -k 65536
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000000000000000000000000000400000000000:80000000000000000000000000007fffffffffff -k 65536 -t %THREADS% -s %STATS% -q
pause
