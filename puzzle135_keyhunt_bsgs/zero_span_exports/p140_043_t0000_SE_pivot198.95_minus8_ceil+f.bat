@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x92095afcfa3abb  tz=2^84
echo stage=SE_pivot198.95_minus8_ceil+form56_mul_2^H2
echo tile 0/4503599627370495  range 92095afcfa3abb000000000000000000000:92095afcfa3abb0000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 92095afcfa3abb000000000000000000000:92095afcfa3abb0000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
