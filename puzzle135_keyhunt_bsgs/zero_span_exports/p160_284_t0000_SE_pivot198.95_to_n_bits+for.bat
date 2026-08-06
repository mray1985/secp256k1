@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x1c63061b50a139  tz=2^107
echo stage=SE_pivot198.95_to_n_bits+form56_div_2^H2
echo tile 0/37778931862957161709567  range e31830da8509c800000000000000000000000000:e31830da8509c8000000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r e31830da8509c800000000000000000000000000:e31830da8509c8000000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
