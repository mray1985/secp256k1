@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x4000ef87d89980a95  tz=2^83
echo stage=SE_pivot198.95_minus8
echo tile 0/2251799813685247  range 200077c3ec4cc054a800000000000000000000:200077c3ec4cc054a8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200077c3ec4cc054a800000000000000000000:200077c3ec4cc054a8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
