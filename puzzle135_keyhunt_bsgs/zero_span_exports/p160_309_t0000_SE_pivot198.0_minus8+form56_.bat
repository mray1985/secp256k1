@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x8000000824cb1ad37ccf  tz=2^80
echo stage=SE_pivot198.0_minus8+form56_mul_sqrt_pN_frac
echo tile 0/281474976710655  range 8000000824cb1ad37ccf00000000000000000000:8000000824cb1ad37ccf000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000000824cb1ad37ccf00000000000000000000:8000000824cb1ad37ccf000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
