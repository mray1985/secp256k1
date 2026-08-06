@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x20000824cb1ad37ccf  tz=2^90
echo stage=SE_pivot199.0_raw+form56_mul_sqrt_pN_frac
echo tile 0/288230376151711743  range 800020932c6b4df33c0000000000000000000000:800020932c6b4df33c00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800020932c6b4df33c0000000000000000000000:800020932c6b4df33c00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
