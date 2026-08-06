@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x101a613e2bfa5a8d  tz=2^89
echo stage=SE_pivot199.0_raw+form56_mul_sqrt_pN_frac
echo tile 0/144115188075855871  range 2034c27c57f4b51a0000000000000000000000:2034c27c57f4b51a00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2034c27c57f4b51a0000000000000000000000:2034c27c57f4b51a00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
