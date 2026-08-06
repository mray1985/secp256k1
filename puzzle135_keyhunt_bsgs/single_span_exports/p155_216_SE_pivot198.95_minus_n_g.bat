@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x20000000000000000000000000001  tz=2^41
echo stage=SE_pivot198.95_minus_n_gap_floor
echo span=2^41  m=2^21  suggested -k 16384
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400000000000000000000000000020000000000:40000000000000000000000000003ffffffffff -k 16384 -t %THREADS% -s %STATS% -q
pause
