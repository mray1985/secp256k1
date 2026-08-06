@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x12095afcfa3abb  tz=2^87
echo stage=SE_pivot198.95_raw_floor+form56_mul_2^H2
echo tile 0/36028797018963967  range 904ad7e7d1d5d8000000000000000000000:904ad7e7d1d5d80000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 904ad7e7d1d5d8000000000000000000000:904ad7e7d1d5d80000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
