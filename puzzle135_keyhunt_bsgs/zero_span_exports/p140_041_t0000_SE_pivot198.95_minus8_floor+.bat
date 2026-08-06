@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x20d271e07f0b379  tz=2^82
echo stage=SE_pivot198.95_minus8_floor+form56_mul_sqrt_pN_frac
echo tile 0/1125899906842623  range 8349c781fc2cde400000000000000000000:8349c781fc2cde4000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8349c781fc2cde400000000000000000000:8349c781fc2cde4000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
