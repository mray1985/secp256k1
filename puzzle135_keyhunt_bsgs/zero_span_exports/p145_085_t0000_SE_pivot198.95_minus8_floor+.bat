@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x801c63061b50a139  tz=2^81
echo stage=SE_pivot198.95_minus8_floor+form56_div_2^H2
echo tile 0/562949953421311  range 10038c60c36a1427200000000000000000000:10038c60c36a14272000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 10038c60c36a1427200000000000000000000:10038c60c36a14272000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
