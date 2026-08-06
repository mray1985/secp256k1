@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x1001  tz=2^142
echo stage=SE_pivot198.95_raw_floor
echo span=2^142  m=2^71  suggested -k 18446744073709551616
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400400000000000000000000000000000000000:4007fffffffffffffffffffffffffffffffffff -k 18446744073709551616 -t %THREADS% -s %STATS% -q
pause
