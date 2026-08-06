@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x1000189cff964876c9  tz=2^81
echo stage=SE_pivot198.95_minus8+form56_mul_sqrt_pN_frac
echo span=2^81  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20003139ff2c90ed9200000000000000000000:20003139ff2c90ed93ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
