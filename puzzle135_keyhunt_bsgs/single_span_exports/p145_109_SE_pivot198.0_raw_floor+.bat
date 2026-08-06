@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x112095afcfa3abb  tz=2^88
echo stage=SE_pivot198.0_raw_floor+form56_mul_2^H2
echo span=2^88  m=2^44  suggested -k 137438953472
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 112095afcfa3abb0000000000000000000000:112095afcfa3abbffffffffffffffffffffff -k 137438953472 -t %THREADS% -s %STATS% -q
pause
