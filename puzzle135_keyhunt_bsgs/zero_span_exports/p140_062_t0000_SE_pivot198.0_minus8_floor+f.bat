@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x80d271e07f0b379  tz=2^80
echo stage=SE_pivot198.0_minus8_floor+form56_mul_sqrt_pN_frac
echo tile 0/281474976710655  range 80d271e07f0b37900000000000000000000:80d271e07f0b379000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 80d271e07f0b37900000000000000000000:80d271e07f0b379000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
