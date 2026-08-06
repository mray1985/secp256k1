@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x2000b33619a93bdf9  tz=2^89
echo stage=SE_pivot198.0_raw
echo tile 0/144115188075855871  range 4001666c335277bf20000000000000000000000:4001666c335277bf200000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4001666c335277bf20000000000000000000000:4001666c335277bf200000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
