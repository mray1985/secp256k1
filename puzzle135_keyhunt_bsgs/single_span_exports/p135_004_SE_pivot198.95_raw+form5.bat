@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 SINGLE-SPAN BSGS  top=0xe4aa253984ce1  tz=2^83
echo stage=SE_pivot198.95_raw+form56_mul_sqrt_pN_frac
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 7255129cc2670800000000000000000000:7255129cc2670fffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
