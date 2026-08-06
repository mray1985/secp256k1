@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x308775f507d97f  tz=2^81
echo stage=SE_pivot198.0_minus8+form56_div_2^H2
echo tile 0/562949953421311  range 610eebea0fb2fe00000000000000000000:610eebea0fb2fe000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 610eebea0fb2fe00000000000000000000:610eebea0fb2fe000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
