@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x1  tz=2^144
echo stage=SE_pivot198.95_to_n_bits
echo span=2^144  m=2^72  suggested -k 36893488147419103232
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1000000000000000000000000000000000000:1ffffffffffffffffffffffffffffffffffff -k 36893488147419103232 -t %THREADS% -s %STATS% -q
pause
