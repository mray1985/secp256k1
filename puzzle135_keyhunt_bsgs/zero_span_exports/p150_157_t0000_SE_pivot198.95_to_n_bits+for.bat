@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x1d271e07f0b379  tz=2^97
echo stage=SE_pivot198.95_to_n_bits+form56_mul_sqrt_pN_frac
echo tile 0/36893488147419103231  range 3a4e3c0fe166f2000000000000000000000000:3a4e3c0fe166f20000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 3a4e3c0fe166f2000000000000000000000000:3a4e3c0fe166f20000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
