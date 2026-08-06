@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x10d271e07f0b379  tz=2^88
echo stage=SE_pivot198.0_raw_ceil+form56_mul_sqrt_pN_frac
echo span=2^88  m=2^44  suggested -k 137438953472
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 10d271e07f0b3790000000000000000000000:10d271e07f0b379ffffffffffffffffffffff -k 137438953472 -t %THREADS% -s %STATS% -q
pause
