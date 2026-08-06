@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x80000013d02e40e87b23  tz=2^80
echo stage=SE_pivot198.0_minus8
echo tile 0/281474976710655  range 80000013d02e40e87b2300000000000000000000:80000013d02e40e87b23000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80000013d02e40e87b2300000000000000000000:80000013d02e40e87b23000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
