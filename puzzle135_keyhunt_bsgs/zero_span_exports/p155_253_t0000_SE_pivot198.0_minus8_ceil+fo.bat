@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x400000d271e07f0b379  tz=2^80
echo stage=SE_pivot198.0_minus8_ceil+form56_mul_sqrt_pN_frac
echo tile 0/281474976710655  range 400000d271e07f0b37900000000000000000000:400000d271e07f0b379000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400000d271e07f0b37900000000000000000000:400000d271e07f0b379000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
