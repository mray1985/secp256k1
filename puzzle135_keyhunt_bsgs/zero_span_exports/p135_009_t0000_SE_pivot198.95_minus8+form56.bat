@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x1e4aa253984ce1  tz=2^82
echo stage=SE_pivot198.95_minus8+form56_mul_sqrt_pN_frac
echo tile 0/1125899906842623  range 792a894e61338400000000000000000000:792a894e613384000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 792a894e61338400000000000000000000:792a894e613384000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
