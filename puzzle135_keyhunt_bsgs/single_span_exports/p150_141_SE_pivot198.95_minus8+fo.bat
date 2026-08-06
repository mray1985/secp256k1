@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x40010e04e23de7239  tz=2^83
echo stage=SE_pivot198.95_minus8+form56_mul_2^H2
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20008702711ef391c800000000000000000000:20008702711ef391cfffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
