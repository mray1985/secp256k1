@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x4000d271e07f0b379  tz=2^88
echo stage=SE_pivot198.0_raw_ceil+form56_mul_sqrt_pN_frac
echo tile 0/72057594037927935  range 4000d271e07f0b3790000000000000000000000:4000d271e07f0b37900000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4000d271e07f0b3790000000000000000000000:4000d271e07f0b37900000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
