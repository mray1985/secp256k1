@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x200005957273d4bc1d  tz=2^90
echo stage=SE_pivot198.0_raw+form56_mul_2^H2
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80001655c9cf52f0740000000000000000000000:80001655c9cf52f077ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
