@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x80000012095afcfa3abb  tz=2^80
echo stage=SE_pivot198.0_minus8_floor+form56_mul_2^H2
echo span=2^80  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80000012095afcfa3abb00000000000000000000:80000012095afcfa3abbffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
