@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x3c63061b50a139  tz=2^81
echo stage=SE_pivot198.0_minus8_ceil+form56_div_2^H2
echo tile 0/562949953421311  range 78c60c36a1427200000000000000000000:78c60c36a14272000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 78c60c36a1427200000000000000000000:78c60c36a14272000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
