@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x21465b19477bdd5  tz=2^82
echo stage=SE_pivot199.0_minus8+form56_mul_sqrt_pN_frac
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 85196c651def75400000000000000000000:85196c651def757ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
