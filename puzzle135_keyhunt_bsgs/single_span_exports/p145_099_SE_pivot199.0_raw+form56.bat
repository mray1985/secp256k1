@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x8fe4f672767acb  tz=2^89
echo stage=SE_pivot199.0_raw+form56_mul_sqrt_pN_frac
echo span=2^89  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 11fc9ece4ecf5960000000000000000000000:11fc9ece4ecf597ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
