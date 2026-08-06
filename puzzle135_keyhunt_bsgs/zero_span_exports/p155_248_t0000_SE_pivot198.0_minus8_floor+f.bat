@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x800001c63061b50a139  tz=2^79
echo stage=SE_pivot198.0_minus8_floor+form56_div_2^H2
echo tile 0/140737488355327  range 400000e31830da8509c80000000000000000000:400000e31830da8509c800000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400000e31830da8509c80000000000000000000:400000e31830da8509c800000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
