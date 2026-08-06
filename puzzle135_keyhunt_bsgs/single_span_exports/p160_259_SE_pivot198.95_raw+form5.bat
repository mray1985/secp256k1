@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x80001e64b958aa0f6d  tz=2^88
echo stage=SE_pivot198.95_raw+form56_mul_sqrt_pN_frac
echo span=2^88  m=2^44  suggested -k 137438953472
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80001e64b958aa0f6d0000000000000000000000:80001e64b958aa0f6dffffffffffffffffffffff -k 137438953472 -t %THREADS% -s %STATS% -q
pause
