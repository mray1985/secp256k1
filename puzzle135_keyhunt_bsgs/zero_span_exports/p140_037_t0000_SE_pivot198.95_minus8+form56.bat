@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x84c200cc43ff59  tz=2^84
echo stage=SE_pivot198.95_minus8+form56_mul_sqrt_pN_frac
echo tile 0/4503599627370495  range 84c200cc43ff59000000000000000000000:84c200cc43ff590000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 84c200cc43ff59000000000000000000000:84c200cc43ff590000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
