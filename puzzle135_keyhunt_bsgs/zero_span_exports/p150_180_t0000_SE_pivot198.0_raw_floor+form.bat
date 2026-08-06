@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x1012095afcfa3abb  tz=2^89
echo stage=SE_pivot198.0_raw_floor+form56_mul_2^H2
echo tile 0/144115188075855871  range 202412b5f9f475760000000000000000000000:202412b5f9f4757600000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 202412b5f9f475760000000000000000000000:202412b5f9f4757600000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
