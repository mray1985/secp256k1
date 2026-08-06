@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x115cbcd3ccf79df  tz=2^88
echo stage=SE_pivot198.0_raw+form56_mul_2^H2
echo tile 0/72057594037927935  range 115cbcd3ccf79df0000000000000000000000:115cbcd3ccf79df00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 115cbcd3ccf79df0000000000000000000000:115cbcd3ccf79df00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
