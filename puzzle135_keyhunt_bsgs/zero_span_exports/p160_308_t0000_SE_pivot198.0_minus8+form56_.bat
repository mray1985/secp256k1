@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x2000000464de13f59e9d  tz=2^82
echo stage=SE_pivot198.0_minus8+form56_div_2^H2
echo tile 0/1125899906842623  range 8000001193784fd67a7400000000000000000000:8000001193784fd67a74000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000001193784fd67a7400000000000000000000:8000001193784fd67a74000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
