@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x9  tz=2^141
echo stage=SE_pivot198.0_raw_ceil
echo span=2^141  m=2^71  suggested -k 18446744073709551616
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1200000000000000000000000000000000000:13fffffffffffffffffffffffffffffffffff -k 18446744073709551616 -t %THREADS% -s %STATS% -q
pause
