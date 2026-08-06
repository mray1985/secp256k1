@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x4001c63061b50a139  tz=2^83
echo stage=SE_pivot199.0_minus8_ceil+form56_div_2^H2
echo tile 0/2251799813685247  range 2000e31830da8509c800000000000000000000:2000e31830da8509c8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2000e31830da8509c800000000000000000000:2000e31830da8509c8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
