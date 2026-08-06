@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x2001c63061b50a139  tz=2^79
echo stage=SE_pivot198.0_minus8_floor+form56_div_2^H2
echo tile 0/140737488355327  range 1000e31830da8509c80000000000000000000:1000e31830da8509c800000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1000e31830da8509c80000000000000000000:1000e31830da8509c800000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
