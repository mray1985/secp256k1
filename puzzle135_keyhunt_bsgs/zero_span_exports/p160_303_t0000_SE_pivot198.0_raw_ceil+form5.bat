@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x400012095afcfa3abb  tz=2^89
echo stage=SE_pivot198.0_raw_ceil+form56_mul_2^H2
echo tile 0/144115188075855871  range 80002412b5f9f475760000000000000000000000:80002412b5f9f4757600000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80002412b5f9f475760000000000000000000000:80002412b5f9f4757600000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
