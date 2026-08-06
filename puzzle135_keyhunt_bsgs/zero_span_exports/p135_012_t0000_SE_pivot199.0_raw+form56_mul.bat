@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x150135e08d0f99  tz=2^82
echo stage=SE_pivot199.0_raw+form56_mul_2^H2
echo tile 0/1125899906842623  range 5404d782343e6400000000000000000000:5404d782343e64000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 5404d782343e6400000000000000000000:5404d782343e64000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
