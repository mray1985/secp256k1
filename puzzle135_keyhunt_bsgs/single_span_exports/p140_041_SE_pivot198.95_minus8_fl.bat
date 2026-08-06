@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x20d271e07f0b379  tz=2^82
echo stage=SE_pivot198.95_minus8_floor+form56_mul_sqrt_pN_frac
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8349c781fc2cde400000000000000000000:8349c781fc2cde7ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
