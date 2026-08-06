@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 SINGLE-SPAN BSGS  top=0x1e4aa253984ce1  tz=2^82
echo stage=SE_pivot198.95_minus8+form56_mul_sqrt_pN_frac
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 792a894e61338400000000000000000000:792a894e613387ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
