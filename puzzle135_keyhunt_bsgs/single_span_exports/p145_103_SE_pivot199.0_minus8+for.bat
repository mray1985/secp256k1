@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x800fe4f672767acb  tz=2^81
echo stage=SE_pivot199.0_minus8+form56_mul_sqrt_pN_frac
echo span=2^81  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1001fc9ece4ecf59600000000000000000000:1001fc9ece4ecf597ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
