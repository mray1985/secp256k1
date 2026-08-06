@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x20000005957273d4bc1d  tz=2^82
echo stage=SE_pivot198.0_minus8+form56_mul_2^H2
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000001655c9cf52f07400000000000000000000:8000001655c9cf52f077ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
