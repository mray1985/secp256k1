@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x20012095afcfa3abb  tz=2^84
echo stage=SE_pivot199.0_minus8_ceil+form56_mul_2^H2
echo tile 0/4503599627370495  range 20012095afcfa3abb000000000000000000000:20012095afcfa3abb0000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20012095afcfa3abb000000000000000000000:20012095afcfa3abb0000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
