@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x40012166374c8b68f  tz=2^83
echo stage=SE_pivot199.0_minus8+form56_mul_2^H2
echo tile 0/2251799813685247  range 200090b31ba645b47800000000000000000000:200090b31ba645b478000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200090b31ba645b47800000000000000000000:200090b31ba645b478000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
