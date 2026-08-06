@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x20000824cb1ad37ccf  tz=2^90
echo stage=SE_pivot199.0_raw+form56_mul_sqrt_pN_frac
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800020932c6b4df33c0000000000000000000000:800020932c6b4df33fffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
