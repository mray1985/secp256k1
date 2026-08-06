@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x400012095afcfa3abb  tz=2^89
echo stage=SE_pivot198.0_raw_ceil+form56_mul_2^H2
echo span=2^89  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80002412b5f9f475760000000000000000000000:80002412b5f9f47577ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
