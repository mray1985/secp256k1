@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x10100b8fbd84099b  tz=2^89
echo stage=SE_pivot198.0_raw
echo tile 0/144115188075855871  range 2020171f7b0813360000000000000000000000:2020171f7b08133600000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2020171f7b0813360000000000000000000000:2020171f7b08133600000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
