@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x80000000000000000000000000001  tz=2^44
echo stage=SE_pivot198.0_minus_n_gap_floor
echo span=2^44  m=2^22  suggested -k 32768
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000000000000000000000000000100000000000:80000000000000000000000000001fffffffffff -k 32768 -t %THREADS% -s %STATS% -q
pause
