@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x12095afcfa3abb  tz=2^107
echo stage=SE_pivot198.95_to_n_bits+form56_mul_2^H2
echo span=2^107  m=2^54  suggested -k 140737488355328
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 904ad7e7d1d5d800000000000000000000000000:904ad7e7d1d5dfffffffffffffffffffffffffff -k 140737488355328 -t %THREADS% -s %STATS% -q
pause
