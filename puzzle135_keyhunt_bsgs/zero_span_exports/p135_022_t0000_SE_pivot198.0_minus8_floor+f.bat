@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x5c63061b50a139  tz=2^80
echo stage=SE_pivot198.0_minus8_floor+form56_div_2^H2
echo tile 0/281474976710655  range 5c63061b50a13900000000000000000000:5c63061b50a139000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 5c63061b50a13900000000000000000000:5c63061b50a139000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
