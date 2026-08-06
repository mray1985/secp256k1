@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x1  tz=2^154
echo stage=SE_pivot198.95_to_n_bits
echo span=2^154  m=2^77  suggested -k 1180591620717411303424
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400000000000000000000000000000000000000:7ffffffffffffffffffffffffffffffffffffff -k 1180591620717411303424 -t %THREADS% -s %STATS% -q
pause
