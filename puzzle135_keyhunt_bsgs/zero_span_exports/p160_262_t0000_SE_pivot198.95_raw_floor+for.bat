@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x40001c63061b50a139  tz=2^89
echo stage=SE_pivot198.95_raw_floor+form56_div_2^H2
echo tile 0/144115188075855871  range 800038c60c36a142720000000000000000000000:800038c60c36a1427200000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800038c60c36a142720000000000000000000000:800038c60c36a1427200000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
