@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x10000a6b714c4c8f2b  tz=2^91
echo stage=SE_pivot198.95_raw+form56_mul_2^H2
echo span=2^91  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000535b8a626479580000000000000000000000:8000535b8a6264795fffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
