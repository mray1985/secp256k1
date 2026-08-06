@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x10000000000000000000000000001  tz=2^47
echo stage=SE_pivot198.95_minus_n_gap_ceil
echo span=2^47  m=2^24  suggested -k 131072
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000000000000000000000000000800000000000:8000000000000000000000000000ffffffffffff -k 131072 -t %THREADS% -s %STATS% -q
pause
