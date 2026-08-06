@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x1ed82f5c47b8a5  tz=2^82
echo stage=SE_pivot198.95_raw+form56_div_2^H2
echo tile 0/1125899906842623  range 7b60bd711ee29400000000000000000000:7b60bd711ee294000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 7b60bd711ee29400000000000000000000:7b60bd711ee294000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
