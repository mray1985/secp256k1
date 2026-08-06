@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x2d271e07f0b379  tz=2^81
echo stage=SE_pivot198.0_minus8_ceil+form56_mul_sqrt_pN_frac
echo tile 0/562949953421311  range 5a4e3c0fe166f200000000000000000000:5a4e3c0fe166f2000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 5a4e3c0fe166f200000000000000000000:5a4e3c0fe166f2000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
