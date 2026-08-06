@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 SINGLE-SPAN BSGS  top=0x13991d60df47d1  tz=2^82
echo stage=SE_pivot198.95_raw+form56_mul_2^H2
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 4e6475837d1f4400000000000000000000:4e6475837d1f47ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
