@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x200000b33619a93bdf9  tz=2^81
echo stage=SE_pivot198.0_minus8
echo tile 0/562949953421311  range 400001666c335277bf200000000000000000000:400001666c335277bf2000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400001666c335277bf200000000000000000000:400001666c335277bf2000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
