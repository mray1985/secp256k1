@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x1000100b8fbd84099b  tz=2^81
echo stage=SE_pivot198.0_minus8
echo tile 0/562949953421311  range 200020171f7b08133600000000000000000000:200020171f7b081336000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200020171f7b08133600000000000000000000:200020171f7b081336000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
