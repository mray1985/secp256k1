@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x2000d271e07f0b379  tz=2^89
echo stage=SE_pivot198.95_raw_floor+form56_mul_sqrt_pN_frac
echo tile 0/144115188075855871  range 4001a4e3c0fe166f20000000000000000000000:4001a4e3c0fe166f200000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4001a4e3c0fe166f20000000000000000000000:4001a4e3c0fe166f200000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
