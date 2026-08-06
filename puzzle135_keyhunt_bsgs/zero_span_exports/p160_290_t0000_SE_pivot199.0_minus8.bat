@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x20000013d02e40e87b23  tz=2^82
echo stage=SE_pivot199.0_minus8
echo tile 0/1125899906842623  range 8000004f40b903a1ec8c00000000000000000000:8000004f40b903a1ec8c000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000004f40b903a1ec8c00000000000000000000:8000004f40b903a1ec8c000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
