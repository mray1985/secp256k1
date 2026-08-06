@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x1  tz=2^159
echo stage=SE_pivot198.95_to_n_bits
echo span=2^159  m=2^80  suggested -k 9444732965739290427392
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000000000000000000000000000000000000000:ffffffffffffffffffffffffffffffffffffffff -k 9444732965739290427392 -t %THREADS% -s %STATS% -q
pause
