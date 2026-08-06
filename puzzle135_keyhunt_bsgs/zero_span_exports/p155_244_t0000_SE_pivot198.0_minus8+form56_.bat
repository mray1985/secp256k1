@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x1000004f7cf4034afc3  tz=2^82
echo stage=SE_pivot198.0_minus8+form56_div_2^H2
echo tile 0/1125899906842623  range 4000013df3d00d2bf0c00000000000000000000:4000013df3d00d2bf0c000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4000013df3d00d2bf0c00000000000000000000:4000013df3d00d2bf0c000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
