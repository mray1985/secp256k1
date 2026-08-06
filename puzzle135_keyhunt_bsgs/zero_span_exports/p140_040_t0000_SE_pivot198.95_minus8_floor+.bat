@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x21c63061b50a139  tz=2^82
echo stage=SE_pivot198.95_minus8_floor+form56_div_2^H2
echo tile 0/1125899906842623  range 8718c186d4284e400000000000000000000:8718c186d4284e4000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8718c186d4284e400000000000000000000:8718c186d4284e4000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
