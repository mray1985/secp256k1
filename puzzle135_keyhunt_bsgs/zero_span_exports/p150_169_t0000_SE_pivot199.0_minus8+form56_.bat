@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x10001a613e2bfa5a8d  tz=2^81
echo stage=SE_pivot199.0_minus8+form56_mul_sqrt_pN_frac
echo tile 0/562949953421311  range 200034c27c57f4b51a00000000000000000000:200034c27c57f4b51a000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200034c27c57f4b51a00000000000000000000:200034c27c57f4b51a000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
