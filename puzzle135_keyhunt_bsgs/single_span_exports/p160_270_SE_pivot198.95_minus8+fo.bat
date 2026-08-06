@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x200000106627679d61b7  tz=2^82
echo stage=SE_pivot198.95_minus8+form56_div_2^H2
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80000041989d9e7586dc00000000000000000000:80000041989d9e7586dfffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
