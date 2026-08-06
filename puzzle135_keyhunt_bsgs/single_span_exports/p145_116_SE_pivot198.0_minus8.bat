@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x1001355c640fb0867  tz=2^80
echo stage=SE_pivot198.0_minus8
echo span=2^80  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1001355c640fb086700000000000000000000:1001355c640fb0867ffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
