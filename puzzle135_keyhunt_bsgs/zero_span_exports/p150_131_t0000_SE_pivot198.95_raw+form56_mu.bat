@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x10189cff964876c9  tz=2^89
echo stage=SE_pivot198.95_raw+form56_mul_sqrt_pN_frac
echo tile 0/144115188075855871  range 203139ff2c90ed920000000000000000000000:203139ff2c90ed9200000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 203139ff2c90ed920000000000000000000000:203139ff2c90ed9200000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
