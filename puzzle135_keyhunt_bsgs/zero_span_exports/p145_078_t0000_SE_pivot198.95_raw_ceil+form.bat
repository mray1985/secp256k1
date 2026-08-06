@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x4d271e07f0b379  tz=2^90
echo stage=SE_pivot198.95_raw_ceil+form56_mul_sqrt_pN_frac
echo tile 0/288230376151711743  range 1349c781fc2cde40000000000000000000000:1349c781fc2cde400000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1349c781fc2cde40000000000000000000000:1349c781fc2cde400000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
