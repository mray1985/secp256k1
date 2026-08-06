@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 SINGLE-SPAN BSGS  top=0x150135e08d0f99  tz=2^82
echo stage=SE_pivot199.0_raw+form56_mul_2^H2
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 5404d782343e6400000000000000000000:5404d782343e67ffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
