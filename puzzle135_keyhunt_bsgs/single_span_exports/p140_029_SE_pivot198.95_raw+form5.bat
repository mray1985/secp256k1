@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x4c200cc43ff59  tz=2^89
echo stage=SE_pivot198.95_raw+form56_mul_sqrt_pN_frac
echo span=2^89  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 984019887feb20000000000000000000000:984019887feb3ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
