@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x9c63061b50a139  tz=2^89
echo stage=SE_pivot198.95_raw_floor+form56_div_2^H2
echo tile 0/144115188075855871  range 138c60c36a142720000000000000000000000:138c60c36a1427200000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 138c60c36a142720000000000000000000000:138c60c36a1427200000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
