@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x100d271e07f0b379  tz=2^89
echo stage=SE_pivot198.95_raw_floor+form56_mul_sqrt_pN_frac
echo span=2^89  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 201a4e3c0fe166f20000000000000000000000:201a4e3c0fe166f3ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
