@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x40000000000000000000000000001  tz=2^40
echo stage=SE_pivot198.0_minus_n_gap_ceil
echo span=2^40  m=2^20  suggested -k 8192
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400000000000000000000000000010000000000:40000000000000000000000000001ffffffffff -k 8192 -t %THREADS% -s %STATS% -q
pause
