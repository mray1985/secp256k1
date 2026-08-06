@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x212095afcfa3abb  tz=2^92
echo stage=SE_pivot199.0_raw_ceil+form56_mul_2^H2
echo span=2^92  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 212095afcfa3abb00000000000000000000000:212095afcfa3abbfffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
