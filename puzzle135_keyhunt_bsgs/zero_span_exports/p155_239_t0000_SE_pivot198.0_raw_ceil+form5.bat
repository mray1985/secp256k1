@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x20012095afcfa3abb  tz=2^89
echo stage=SE_pivot198.0_raw_ceil+form56_mul_2^H2
echo tile 0/144115188075855871  range 4002412b5f9f475760000000000000000000000:4002412b5f9f4757600000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4002412b5f9f475760000000000000000000000:4002412b5f9f4757600000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
