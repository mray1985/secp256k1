@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x20000013d02e40e87b23  tz=2^82
echo stage=SE_pivot199.0_minus8
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000004f40b903a1ec8c00000000000000000000:8000004f40b903a1ec8fffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
