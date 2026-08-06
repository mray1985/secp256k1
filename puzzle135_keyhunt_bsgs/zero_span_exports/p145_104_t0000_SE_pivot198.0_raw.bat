@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x11355c640fb0867  tz=2^88
echo stage=SE_pivot198.0_raw
echo tile 0/72057594037927935  range 11355c640fb08670000000000000000000000:11355c640fb086700000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 11355c640fb08670000000000000000000000:11355c640fb086700000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
