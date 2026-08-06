@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x81465b19477bdd5  tz=2^80
echo stage=SE_pivot198.0_minus8+form56_mul_sqrt_pN_frac
echo tile 0/281474976710655  range 81465b19477bdd500000000000000000000:81465b19477bdd5000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 81465b19477bdd500000000000000000000:81465b19477bdd5000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
