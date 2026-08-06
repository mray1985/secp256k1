@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x80000013d02e40e87b23  tz=2^80
echo stage=SE_pivot198.0_minus8
echo span=2^80  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80000013d02e40e87b2300000000000000000000:80000013d02e40e87b23ffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
