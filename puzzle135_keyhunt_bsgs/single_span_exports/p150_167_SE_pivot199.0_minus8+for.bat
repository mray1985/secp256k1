@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x40012166374c8b68f  tz=2^83
echo stage=SE_pivot199.0_minus8+form56_mul_2^H2
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200090b31ba645b47800000000000000000000:200090b31ba645b47fffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
