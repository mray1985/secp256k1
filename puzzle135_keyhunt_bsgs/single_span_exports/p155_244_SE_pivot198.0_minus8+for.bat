@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x1000004f7cf4034afc3  tz=2^82
echo stage=SE_pivot198.0_minus8+form56_div_2^H2
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4000013df3d00d2bf0c00000000000000000000:4000013df3d00d2bf0fffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
