@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x10100b8fbd84099b  tz=2^89
echo stage=SE_pivot198.0_raw
echo span=2^89  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2020171f7b0813360000000000000000000000:2020171f7b081337ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
