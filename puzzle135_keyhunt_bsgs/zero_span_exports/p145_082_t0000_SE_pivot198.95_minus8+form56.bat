@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x1001da8f3ee0d2e39  tz=2^80
echo stage=SE_pivot198.95_minus8+form56_mul_sqrt_pN_frac
echo tile 0/281474976710655  range 1001da8f3ee0d2e3900000000000000000000:1001da8f3ee0d2e39000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1001da8f3ee0d2e3900000000000000000000:1001da8f3ee0d2e39000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
