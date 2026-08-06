@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x4015cbcd3ccf79df  tz=2^82
echo stage=SE_pivot199.0_minus8+form56_mul_2^H2
echo tile 0/1125899906842623  range 100572f34f33de77c00000000000000000000:100572f34f33de77c000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 100572f34f33de77c00000000000000000000:100572f34f33de77c000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
