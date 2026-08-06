@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x14829361c760ed  tz=2^92
echo stage=SE_pivot198.95_raw
echo tile 0/1152921504606846975  range 14829361c760ed00000000000000000000000:14829361c760ed000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 14829361c760ed00000000000000000000000:14829361c760ed000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
