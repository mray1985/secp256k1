@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x412095afcfa3abb  tz=2^91
echo stage=SE_pivot198.95_raw_ceil+form56_mul_2^H2
echo tile 0/576460752303423487  range 20904ad7e7d1d5d80000000000000000000000:20904ad7e7d1d5d800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20904ad7e7d1d5d80000000000000000000000:20904ad7e7d1d5d800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
