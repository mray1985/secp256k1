@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x10189cff964876c9  tz=2^89
echo stage=SE_pivot198.95_raw+form56_mul_sqrt_pN_frac
echo span=2^89  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 203139ff2c90ed920000000000000000000000:203139ff2c90ed93ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
