@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x2000000824cb1ad37ccf  tz=2^82
echo stage=SE_pivot199.0_minus8+form56_mul_sqrt_pN_frac
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80000020932c6b4df33c00000000000000000000:80000020932c6b4df33fffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
