@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x8000d271e07f0b379  tz=2^82
echo stage=SE_pivot198.95_minus8_ceil+form56_mul_sqrt_pN_frac
echo tile 0/1125899906842623  range 2000349c781fc2cde400000000000000000000:2000349c781fc2cde4000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2000349c781fc2cde400000000000000000000:2000349c781fc2cde4000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
