@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x12095afcfa3abb  tz=2^97
echo stage=SE_pivot198.95_to_n_bits+form56_mul_2^H2
echo span=2^97  m=2^49  suggested -k 4398046511104
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2412b5f9f47576000000000000000000000000:2412b5f9f47577ffffffffffffffffffffffff -k 4398046511104 -t %THREADS% -s %STATS% -q
pause
