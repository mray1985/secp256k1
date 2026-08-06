@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x1000014e6b8feddc2a7  tz=2^82
echo stage=SE_pivot198.95_minus8
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40000539ae3fb770a9c00000000000000000000:40000539ae3fb770a9fffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
