@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x1000100b8fbd84099b  tz=2^81
echo stage=SE_pivot198.0_minus8
echo span=2^81  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200020171f7b08133600000000000000000000:200020171f7b081337ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
