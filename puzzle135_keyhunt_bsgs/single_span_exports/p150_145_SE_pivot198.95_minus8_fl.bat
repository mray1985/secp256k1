@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x80012095afcfa3abb  tz=2^82
echo stage=SE_pivot198.95_minus8_floor+form56_mul_2^H2
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200048256bf3e8eaec00000000000000000000:200048256bf3e8eaefffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
