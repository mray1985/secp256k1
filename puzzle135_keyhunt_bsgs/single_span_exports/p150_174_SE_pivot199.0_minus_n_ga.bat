@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x8000000000000000000000000001  tz=2^38
echo stage=SE_pivot199.0_minus_n_gap_ceil
echo span=2^38  m=2^19  suggested -k 4096
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20000000000000000000000000004000000000:20000000000000000000000000007fffffffff -k 4096 -t %THREADS% -s %STATS% -q
pause
