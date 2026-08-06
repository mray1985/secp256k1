@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x80000000000000000000000000001  tz=2^39
echo stage=SE_pivot198.0_minus_n_gap_floor
echo span=2^39  m=2^20  suggested -k 8192
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400000000000000000000000000008000000000:40000000000000000000000000000ffffffffff -k 8192 -t %THREADS% -s %STATS% -q
pause
