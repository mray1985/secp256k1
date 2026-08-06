@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x1000d271e07f0b379  tz=2^80
echo stage=SE_pivot198.0_minus8_ceil+form56_mul_sqrt_pN_frac
echo tile 0/281474976710655  range 1000d271e07f0b37900000000000000000000:1000d271e07f0b379000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1000d271e07f0b37900000000000000000000:1000d271e07f0b379000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
