@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x40001a613e2bfa5a8d  tz=2^79
echo stage=SE_pivot198.0_minus8+form56_mul_sqrt_pN_frac
echo span=2^79  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20000d309f15fd2d4680000000000000000000:20000d309f15fd2d46ffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
