@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x1004829361c760ed  tz=2^84
echo stage=SE_pivot198.95_minus8
echo span=2^84  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1004829361c760ed000000000000000000000:1004829361c760edfffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
