@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x10000001c63061b50a139  tz=2^79
echo stage=SE_pivot198.0_minus8_floor+form56_div_2^H2
echo span=2^79  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000000e31830da8509c80000000000000000000:8000000e31830da8509cffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
