@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x4100b8fbd84099b  tz=2^91
echo stage=SE_pivot199.0_raw
echo span=2^91  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20805c7dec204cd80000000000000000000000:20805c7dec204cdfffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
