@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x8012095afcfa3abb  tz=2^91
echo stage=SE_pivot198.95_raw_ceil+form56_mul_2^H2
echo tile 0/576460752303423487  range 400904ad7e7d1d5d80000000000000000000000:400904ad7e7d1d5d800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400904ad7e7d1d5d80000000000000000000000:400904ad7e7d1d5d800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
