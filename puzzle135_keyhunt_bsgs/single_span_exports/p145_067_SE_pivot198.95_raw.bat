@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x14829361c760ed  tz=2^92
echo stage=SE_pivot198.95_raw
echo span=2^92  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 14829361c760ed00000000000000000000000:14829361c760edfffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
