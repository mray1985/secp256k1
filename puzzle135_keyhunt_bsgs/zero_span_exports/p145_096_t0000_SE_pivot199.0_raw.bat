@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x5355c640fb0867  tz=2^90
echo stage=SE_pivot199.0_raw
echo tile 0/288230376151711743  range 14d571903ec219c0000000000000000000000:14d571903ec219c00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 14d571903ec219c0000000000000000000000:14d571903ec219c00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
