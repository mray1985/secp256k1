@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x400100b8fbd84099b  tz=2^83
echo stage=SE_pivot199.0_minus8
echo tile 0/2251799813685247  range 2000805c7dec204cd800000000000000000000:2000805c7dec204cd8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2000805c7dec204cd800000000000000000000:2000805c7dec204cd8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
