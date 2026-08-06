@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x401c63061b50a139  tz=2^82
echo stage=SE_pivot198.95_minus8_ceil+form56_div_2^H2
echo tile 0/1125899906842623  range 100718c186d4284e400000000000000000000:100718c186d4284e4000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 100718c186d4284e400000000000000000000:100718c186d4284e4000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
