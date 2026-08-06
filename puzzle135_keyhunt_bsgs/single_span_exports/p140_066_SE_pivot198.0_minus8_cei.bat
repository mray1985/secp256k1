@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x40d271e07f0b379  tz=2^81
echo stage=SE_pivot198.0_minus8_ceil+form56_mul_sqrt_pN_frac
echo span=2^81  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 81a4e3c0fe166f200000000000000000000:81a4e3c0fe166f3ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
