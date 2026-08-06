@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x11c63061b50a139  tz=2^83
echo stage=SE_pivot198.95_minus8_ceil+form56_div_2^H2
echo tile 0/2251799813685247  range 8e31830da8509c800000000000000000000:8e31830da8509c8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8e31830da8509c800000000000000000000:8e31830da8509c8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
