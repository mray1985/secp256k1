@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x2000ca05a66ea9b87  tz=2^89
echo stage=SE_pivot198.0_raw+form56_mul_2^H2
echo tile 0/144115188075855871  range 4001940b4cdd5370e0000000000000000000000:4001940b4cdd5370e00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4001940b4cdd5370e0000000000000000000000:4001940b4cdd5370e00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
