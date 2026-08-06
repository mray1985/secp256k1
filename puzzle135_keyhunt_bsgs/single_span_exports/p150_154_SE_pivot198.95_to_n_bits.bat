@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x1  tz=2^149
echo stage=SE_pivot198.95_to_n_bits
echo span=2^149  m=2^75  suggested -k 295147905179352825856
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20000000000000000000000000000000000000:3fffffffffffffffffffffffffffffffffffff -k 295147905179352825856 -t %THREADS% -s %STATS% -q
pause
