@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x800012095afcfa3abb  tz=2^83
echo stage=SE_pivot198.95_minus8_ceil+form56_mul_2^H2
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40000904ad7e7d1d5d800000000000000000000:40000904ad7e7d1d5dfffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
