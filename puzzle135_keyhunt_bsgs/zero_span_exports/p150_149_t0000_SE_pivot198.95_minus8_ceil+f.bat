@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x40012095afcfa3abb  tz=2^83
echo stage=SE_pivot198.95_minus8_ceil+form56_mul_2^H2
echo tile 0/2251799813685247  range 2000904ad7e7d1d5d800000000000000000000:2000904ad7e7d1d5d8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2000904ad7e7d1d5d800000000000000000000:2000904ad7e7d1d5d8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
