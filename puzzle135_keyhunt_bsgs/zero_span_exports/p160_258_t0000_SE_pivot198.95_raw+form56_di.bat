@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x2000106627679d61b7  tz=2^90
echo stage=SE_pivot198.95_raw+form56_div_2^H2
echo tile 0/288230376151711743  range 800041989d9e7586dc0000000000000000000000:800041989d9e7586dc00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800041989d9e7586dc0000000000000000000000:800041989d9e7586dc00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
