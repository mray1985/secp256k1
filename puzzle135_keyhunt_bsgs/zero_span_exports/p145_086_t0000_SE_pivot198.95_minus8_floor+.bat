@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x800d271e07f0b379  tz=2^81
echo stage=SE_pivot198.95_minus8_floor+form56_mul_sqrt_pN_frac
echo tile 0/562949953421311  range 1001a4e3c0fe166f200000000000000000000:1001a4e3c0fe166f2000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1001a4e3c0fe166f200000000000000000000:1001a4e3c0fe166f2000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
