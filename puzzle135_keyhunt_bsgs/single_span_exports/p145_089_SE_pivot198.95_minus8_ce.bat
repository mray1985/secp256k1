@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x401c63061b50a139  tz=2^82
echo stage=SE_pivot198.95_minus8_ceil+form56_div_2^H2
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 100718c186d4284e400000000000000000000:100718c186d4284e7ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
