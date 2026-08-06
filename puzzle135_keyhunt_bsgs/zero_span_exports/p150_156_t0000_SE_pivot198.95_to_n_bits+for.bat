@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x1c63061b50a139  tz=2^97
echo stage=SE_pivot198.95_to_n_bits+form56_div_2^H2
echo tile 0/36893488147419103231  range 38c60c36a14272000000000000000000000000:38c60c36a142720000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 38c60c36a14272000000000000000000000000:38c60c36a142720000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
