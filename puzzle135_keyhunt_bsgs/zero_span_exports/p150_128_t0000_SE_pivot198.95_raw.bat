@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x40ef87d89980a95  tz=2^91
echo stage=SE_pivot198.95_raw
echo tile 0/576460752303423487  range 2077c3ec4cc054a80000000000000000000000:2077c3ec4cc054a800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2077c3ec4cc054a80000000000000000000000:2077c3ec4cc054a800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
