@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x400100b8fbd84099b  tz=2^83
echo stage=SE_pivot199.0_minus8
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2000805c7dec204cd800000000000000000000:2000805c7dec204cdfffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
