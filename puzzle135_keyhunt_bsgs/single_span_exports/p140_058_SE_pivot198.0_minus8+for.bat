@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x81465b19477bdd5  tz=2^80
echo stage=SE_pivot198.0_minus8+form56_mul_sqrt_pN_frac
echo span=2^80  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 81465b19477bdd500000000000000000000:81465b19477bdd5ffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
