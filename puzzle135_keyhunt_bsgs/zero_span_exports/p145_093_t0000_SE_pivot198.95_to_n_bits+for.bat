@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x12095afcfa3abb  tz=2^92
echo stage=SE_pivot198.95_to_n_bits+form56_mul_2^H2
echo tile 0/1152921504606846975  range 12095afcfa3abb00000000000000000000000:12095afcfa3abb000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 12095afcfa3abb00000000000000000000000:12095afcfa3abb000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
