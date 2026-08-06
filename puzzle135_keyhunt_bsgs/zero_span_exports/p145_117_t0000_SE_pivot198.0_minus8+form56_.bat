@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x10015cbcd3ccf79df  tz=2^80
echo stage=SE_pivot198.0_minus8+form56_mul_2^H2
echo tile 0/281474976710655  range 10015cbcd3ccf79df00000000000000000000:10015cbcd3ccf79df000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 10015cbcd3ccf79df00000000000000000000:10015cbcd3ccf79df000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
