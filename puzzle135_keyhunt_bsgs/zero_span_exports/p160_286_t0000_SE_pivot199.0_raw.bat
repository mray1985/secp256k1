@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x200013d02e40e87b23  tz=2^90
echo stage=SE_pivot199.0_raw
echo tile 0/288230376151711743  range 80004f40b903a1ec8c0000000000000000000000:80004f40b903a1ec8c00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80004f40b903a1ec8c0000000000000000000000:80004f40b903a1ec8c00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
