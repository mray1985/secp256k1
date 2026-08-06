@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x10014e6b8feddc2a7  tz=2^90
echo stage=SE_pivot198.95_raw
echo tile 0/288230376151711743  range 400539ae3fb770a9c0000000000000000000000:400539ae3fb770a9c00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400539ae3fb770a9c0000000000000000000000:400539ae3fb770a9c00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
