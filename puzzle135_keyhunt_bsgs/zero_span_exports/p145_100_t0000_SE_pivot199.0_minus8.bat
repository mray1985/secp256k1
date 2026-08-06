@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x401355c640fb0867  tz=2^82
echo stage=SE_pivot199.0_minus8
echo tile 0/1125899906842623  range 1004d571903ec219c00000000000000000000:1004d571903ec219c000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1004d571903ec219c00000000000000000000:1004d571903ec219c000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
