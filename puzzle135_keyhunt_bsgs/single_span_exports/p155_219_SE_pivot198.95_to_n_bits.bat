@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x12095afcfa3abb  tz=2^102
echo stage=SE_pivot198.95_to_n_bits+form56_mul_2^H2
echo span=2^102  m=2^51  suggested -k 17592186044416
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 48256bf3e8eaec0000000000000000000000000:48256bf3e8eaeffffffffffffffffffffffffff -k 17592186044416 -t %THREADS% -s %STATS% -q
pause
