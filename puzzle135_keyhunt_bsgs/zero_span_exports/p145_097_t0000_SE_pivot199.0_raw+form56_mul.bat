@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x55cbcd3ccf79df  tz=2^90
echo stage=SE_pivot199.0_raw+form56_mul_2^H2
echo tile 0/288230376151711743  range 1572f34f33de77c0000000000000000000000:1572f34f33de77c00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1572f34f33de77c0000000000000000000000:1572f34f33de77c00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
