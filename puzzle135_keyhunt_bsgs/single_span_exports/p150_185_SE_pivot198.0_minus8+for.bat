@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x400038ef12698bedd  tz=2^83
echo stage=SE_pivot198.0_minus8+form56_div_2^H2
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20001c778934c5f6e800000000000000000000:20001c778934c5f6efffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
