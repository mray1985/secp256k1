@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x41c63061b50a139  tz=2^91
echo stage=SE_pivot199.0_raw_ceil+form56_div_2^H2
echo tile 0/576460752303423487  range 20e31830da8509c80000000000000000000000:20e31830da8509c800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20e31830da8509c80000000000000000000000:20e31830da8509c800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
