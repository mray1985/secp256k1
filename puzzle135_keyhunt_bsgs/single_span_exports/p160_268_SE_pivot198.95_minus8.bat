@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x200000127c830ca26243  tz=2^82
echo stage=SE_pivot198.95_minus8
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80000049f20c3289890c00000000000000000000:80000049f20c3289890fffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
