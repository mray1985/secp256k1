@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x2001c63061b50a139  tz=2^79
echo stage=SE_pivot198.0_minus8_floor+form56_div_2^H2
echo span=2^79  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1000e31830da8509c80000000000000000000:1000e31830da8509cffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
