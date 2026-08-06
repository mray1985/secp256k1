@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x1000014e6b8feddc2a7  tz=2^82
echo stage=SE_pivot198.95_minus8
echo tile 0/1125899906842623  range 40000539ae3fb770a9c00000000000000000000:40000539ae3fb770a9c000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40000539ae3fb770a9c00000000000000000000:40000539ae3fb770a9c000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
