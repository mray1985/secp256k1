@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x10001c63061b50a139  tz=2^81
echo stage=SE_pivot198.95_minus8_floor+form56_div_2^H2
echo tile 0/562949953421311  range 200038c60c36a1427200000000000000000000:200038c60c36a14272000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200038c60c36a1427200000000000000000000:200038c60c36a14272000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
