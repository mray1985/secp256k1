@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x1c63061b50a139  tz=2^92
echo stage=SE_pivot198.95_to_n_bits+form56_div_2^H2
echo tile 0/1152921504606846975  range 1c63061b50a13900000000000000000000000:1c63061b50a139000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1c63061b50a13900000000000000000000000:1c63061b50a139000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
