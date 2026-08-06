@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x100001c63061b50a139  tz=2^87
echo stage=SE_pivot198.0_raw_floor+form56_div_2^H2
echo tile 0/36028797018963967  range 80000e31830da8509c8000000000000000000000:80000e31830da8509c80000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80000e31830da8509c8000000000000000000000:80000e31830da8509c80000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
