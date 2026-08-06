@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x212095afcfa3abb  tz=2^82
echo stage=SE_pivot198.0_minus8_ceil+form56_mul_2^H2
echo tile 0/1125899906842623  range 848256bf3e8eaec00000000000000000000:848256bf3e8eaec000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 848256bf3e8eaec00000000000000000000:848256bf3e8eaec000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
