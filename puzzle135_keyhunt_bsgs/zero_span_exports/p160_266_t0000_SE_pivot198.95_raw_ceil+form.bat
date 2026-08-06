@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x20001c63061b50a139  tz=2^90
echo stage=SE_pivot198.95_raw_ceil+form56_div_2^H2
echo tile 0/288230376151711743  range 8000718c186d4284e40000000000000000000000:8000718c186d4284e400000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000718c186d4284e40000000000000000000000:8000718c186d4284e400000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
