@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x20000d271e07f0b379  tz=2^80
echo stage=SE_pivot198.0_minus8_floor+form56_mul_sqrt_pN_frac
echo span=2^80  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20000d271e07f0b37900000000000000000000:20000d271e07f0b379ffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
