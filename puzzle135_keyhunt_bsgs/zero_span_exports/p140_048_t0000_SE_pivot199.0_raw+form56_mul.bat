@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x37f11a2b69623  tz=2^90
echo stage=SE_pivot199.0_raw+form56_mul_2^H2
echo tile 0/288230376151711743  range dfc468ada588c0000000000000000000000:dfc468ada588c00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r dfc468ada588c0000000000000000000000:dfc468ada588c00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
