@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x101a613e2bfa5a8d  tz=2^89
echo stage=SE_pivot199.0_raw+form56_mul_sqrt_pN_frac
echo span=2^89  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2034c27c57f4b51a0000000000000000000000:2034c27c57f4b51bffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
