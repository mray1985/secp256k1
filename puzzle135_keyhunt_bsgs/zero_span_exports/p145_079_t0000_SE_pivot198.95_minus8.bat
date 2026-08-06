@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x1004829361c760ed  tz=2^84
echo stage=SE_pivot198.95_minus8
echo tile 0/4503599627370495  range 1004829361c760ed000000000000000000000:1004829361c760ed0000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1004829361c760ed000000000000000000000:1004829361c760ed0000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
