@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x20c6804def9f3b1  tz=2^82
echo stage=SE_pivot198.0_minus8
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 831a0137be7cec400000000000000000000:831a0137be7cec7ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
