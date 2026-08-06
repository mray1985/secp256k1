@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x8000001c63061b50a139  tz=2^80
echo stage=SE_pivot198.0_minus8_ceil+form56_div_2^H2
echo span=2^80  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000001c63061b50a13900000000000000000000:8000001c63061b50a139ffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
