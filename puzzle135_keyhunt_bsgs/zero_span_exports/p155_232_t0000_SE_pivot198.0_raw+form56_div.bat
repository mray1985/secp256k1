@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x10004f7cf4034afc3  tz=2^90
echo stage=SE_pivot198.0_raw+form56_div_2^H2
echo tile 0/288230376151711743  range 40013df3d00d2bf0c0000000000000000000000:40013df3d00d2bf0c00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40013df3d00d2bf0c0000000000000000000000:40013df3d00d2bf0c00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
