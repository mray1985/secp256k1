@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x800013d02e40e87b23  tz=2^88
echo stage=SE_pivot198.0_raw
echo tile 0/72057594037927935  range 800013d02e40e87b230000000000000000000000:800013d02e40e87b2300000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800013d02e40e87b230000000000000000000000:800013d02e40e87b2300000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
