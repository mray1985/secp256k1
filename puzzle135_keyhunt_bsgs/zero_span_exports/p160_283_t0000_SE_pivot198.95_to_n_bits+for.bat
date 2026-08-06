@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x12095afcfa3abb  tz=2^107
echo stage=SE_pivot198.95_to_n_bits+form56_mul_2^H2
echo tile 0/37778931862957161709567  range 904ad7e7d1d5d800000000000000000000000000:904ad7e7d1d5d8000000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 904ad7e7d1d5d800000000000000000000000000:904ad7e7d1d5d8000000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
