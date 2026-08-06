@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x200001c63061b50a139  tz=2^81
echo stage=SE_pivot198.95_minus8_floor+form56_div_2^H2
echo tile 0/562949953421311  range 4000038c60c36a1427200000000000000000000:4000038c60c36a14272000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4000038c60c36a1427200000000000000000000:4000038c60c36a14272000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
