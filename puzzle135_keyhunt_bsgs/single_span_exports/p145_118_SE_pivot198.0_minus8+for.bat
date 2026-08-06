@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x400449b8a1b2bcd3  tz=2^82
echo stage=SE_pivot198.0_minus8+form56_div_2^H2
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1001126e286caf34c00000000000000000000:1001126e286caf34fffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
