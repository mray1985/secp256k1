@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x100012166374c8b68f  tz=2^81
echo stage=SE_pivot198.0_minus8+form56_mul_2^H2
echo span=2^81  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2000242cc6e9916d1e00000000000000000000:2000242cc6e9916d1fffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
