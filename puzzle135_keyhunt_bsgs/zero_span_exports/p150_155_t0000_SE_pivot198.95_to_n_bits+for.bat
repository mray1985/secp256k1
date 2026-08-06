@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x12095afcfa3abb  tz=2^97
echo stage=SE_pivot198.95_to_n_bits+form56_mul_2^H2
echo tile 0/36893488147419103231  range 2412b5f9f47576000000000000000000000000:2412b5f9f475760000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2412b5f9f47576000000000000000000000000:2412b5f9f475760000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
