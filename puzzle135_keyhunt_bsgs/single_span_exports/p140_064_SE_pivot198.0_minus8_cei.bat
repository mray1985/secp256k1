@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x212095afcfa3abb  tz=2^82
echo stage=SE_pivot198.0_minus8_ceil+form56_mul_2^H2
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 848256bf3e8eaec00000000000000000000:848256bf3e8eaefffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
