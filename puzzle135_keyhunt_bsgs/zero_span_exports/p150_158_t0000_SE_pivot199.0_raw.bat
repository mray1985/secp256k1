@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x4100b8fbd84099b  tz=2^91
echo stage=SE_pivot199.0_raw
echo tile 0/576460752303423487  range 20805c7dec204cd80000000000000000000000:20805c7dec204cd800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20805c7dec204cd80000000000000000000000:20805c7dec204cd800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
