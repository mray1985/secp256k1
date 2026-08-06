@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x1012166374c8b68f  tz=2^89
echo stage=SE_pivot198.0_raw+form56_mul_2^H2
echo span=2^89  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20242cc6e9916d1e0000000000000000000000:20242cc6e9916d1fffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
