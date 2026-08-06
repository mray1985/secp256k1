@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x1000d271e07f0b379  tz=2^90
echo stage=SE_pivot198.95_raw_ceil+form56_mul_sqrt_pN_frac
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400349c781fc2cde40000000000000000000000:400349c781fc2cde7ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
