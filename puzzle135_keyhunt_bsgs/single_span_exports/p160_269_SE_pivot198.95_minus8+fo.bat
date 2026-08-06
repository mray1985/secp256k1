@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x1000000a6b714c4c8f2b  tz=2^83
echo stage=SE_pivot198.95_minus8+form56_mul_2^H2
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800000535b8a6264795800000000000000000000:800000535b8a6264795fffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
