@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x1c63061b50a139  tz=2^87
echo stage=SE_pivot198.95_raw_floor+form56_div_2^H2
echo tile 0/36028797018963967  range e31830da8509c8000000000000000000000:e31830da8509c80000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r e31830da8509c8000000000000000000000:e31830da8509c80000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
