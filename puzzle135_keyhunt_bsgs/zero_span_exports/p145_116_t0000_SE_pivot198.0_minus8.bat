@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x1001355c640fb0867  tz=2^80
echo stage=SE_pivot198.0_minus8
echo tile 0/281474976710655  range 1001355c640fb086700000000000000000000:1001355c640fb0867000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1001355c640fb086700000000000000000000:1001355c640fb0867000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
