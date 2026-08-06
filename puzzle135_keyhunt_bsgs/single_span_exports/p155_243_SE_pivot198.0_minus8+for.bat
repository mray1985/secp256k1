@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x200000ca05a66ea9b87  tz=2^81
echo stage=SE_pivot198.0_minus8+form56_mul_2^H2
echo span=2^81  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400001940b4cdd5370e00000000000000000000:400001940b4cdd5370fffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
