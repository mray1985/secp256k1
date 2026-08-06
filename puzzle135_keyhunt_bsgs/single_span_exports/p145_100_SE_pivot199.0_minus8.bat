@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x401355c640fb0867  tz=2^82
echo stage=SE_pivot199.0_minus8
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1004d571903ec219c00000000000000000000:1004d571903ec219fffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
