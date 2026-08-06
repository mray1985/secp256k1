@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x2000000824cb1ad37ccf  tz=2^82
echo stage=SE_pivot199.0_minus8+form56_mul_sqrt_pN_frac
echo tile 0/1125899906842623  range 80000020932c6b4df33c00000000000000000000:80000020932c6b4df33c000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80000020932c6b4df33c00000000000000000000:80000020932c6b4df33c000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
