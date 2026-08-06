@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x21465b19477bdd5  tz=2^82
echo stage=SE_pivot199.0_minus8+form56_mul_sqrt_pN_frac
echo tile 0/1125899906842623  range 85196c651def75400000000000000000000:85196c651def754000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 85196c651def75400000000000000000000:85196c651def754000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
