@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x200012095afcfa3abb  tz=2^90
echo stage=SE_pivot198.95_raw_floor+form56_mul_2^H2
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800048256bf3e8eaec0000000000000000000000:800048256bf3e8eaefffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
