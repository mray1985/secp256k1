@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x8000001e64b958aa0f6d  tz=2^80
echo stage=SE_pivot198.95_minus8+form56_mul_sqrt_pN_frac
echo span=2^80  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000001e64b958aa0f6d00000000000000000000:8000001e64b958aa0f6dffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
