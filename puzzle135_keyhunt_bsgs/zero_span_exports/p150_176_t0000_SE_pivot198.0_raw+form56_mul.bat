@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x1012166374c8b68f  tz=2^89
echo stage=SE_pivot198.0_raw+form56_mul_2^H2
echo tile 0/144115188075855871  range 20242cc6e9916d1e0000000000000000000000:20242cc6e9916d1e00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20242cc6e9916d1e0000000000000000000000:20242cc6e9916d1e00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
