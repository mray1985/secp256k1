@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x212095afcfa3abb  tz=2^92
echo stage=SE_pivot199.0_raw_ceil+form56_mul_2^H2
echo tile 0/1152921504606846975  range 212095afcfa3abb00000000000000000000000:212095afcfa3abb000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 212095afcfa3abb00000000000000000000000:212095afcfa3abb000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
