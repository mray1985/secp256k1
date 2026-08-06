@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x10001a613e2bfa5a8d  tz=2^81
echo stage=SE_pivot199.0_minus8+form56_mul_sqrt_pN_frac
echo span=2^81  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200034c27c57f4b51a00000000000000000000:200034c27c57f4b51bffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
