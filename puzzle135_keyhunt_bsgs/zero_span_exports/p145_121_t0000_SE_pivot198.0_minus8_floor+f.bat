@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x10012095afcfa3abb  tz=2^80
echo stage=SE_pivot198.0_minus8_floor+form56_mul_2^H2
echo tile 0/281474976710655  range 10012095afcfa3abb00000000000000000000:10012095afcfa3abb000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 10012095afcfa3abb00000000000000000000:10012095afcfa3abb000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
