@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x4c200cc43ff59  tz=2^89
echo stage=SE_pivot198.95_raw+form56_mul_sqrt_pN_frac
echo tile 0/144115188075855871  range 984019887feb20000000000000000000000:984019887feb200000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 984019887feb20000000000000000000000:984019887feb200000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
