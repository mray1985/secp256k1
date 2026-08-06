@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x55cbcd3ccf79df  tz=2^90
echo stage=SE_pivot199.0_raw+form56_mul_2^H2
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1572f34f33de77c0000000000000000000000:1572f34f33de77fffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
