@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x200000106627679d61b7  tz=2^82
echo stage=SE_pivot198.95_minus8+form56_div_2^H2
echo tile 0/1125899906842623  range 80000041989d9e7586dc00000000000000000000:80000041989d9e7586dc000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80000041989d9e7586dc00000000000000000000:80000041989d9e7586dc000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
