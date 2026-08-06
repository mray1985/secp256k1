@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x101  tz=2^141
echo stage=SE_pivot198.0_raw_floor
echo span=2^141  m=2^71  suggested -k 18446744073709551616
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20200000000000000000000000000000000000:203fffffffffffffffffffffffffffffffffff -k 18446744073709551616 -t %THREADS% -s %STATS% -q
pause
