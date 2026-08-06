@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x5c63061b50a139  tz=2^90
echo stage=SE_pivot198.95_raw_ceil+form56_div_2^H2
echo tile 0/288230376151711743  range 1718c186d4284e40000000000000000000000:1718c186d4284e400000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1718c186d4284e40000000000000000000000:1718c186d4284e400000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
