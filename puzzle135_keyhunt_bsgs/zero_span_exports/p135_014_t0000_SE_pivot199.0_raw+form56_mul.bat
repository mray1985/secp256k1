@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x1ea2742f79c4e5  tz=2^82
echo stage=SE_pivot199.0_raw+form56_mul_sqrt_pN_frac
echo tile 0/1125899906842623  range 7a89d0bde7139400000000000000000000:7a89d0bde71394000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 7a89d0bde7139400000000000000000000:7a89d0bde71394000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
