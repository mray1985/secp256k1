@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x2000fe4f672767acb  tz=2^79
echo stage=SE_pivot198.0_minus8+form56_mul_sqrt_pN_frac
echo span=2^79  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 10007f27b393b3d6580000000000000000000:10007f27b393b3d65ffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
