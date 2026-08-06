@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x2000106627679d61b7  tz=2^90
echo stage=SE_pivot198.95_raw+form56_div_2^H2
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800041989d9e7586dc0000000000000000000000:800041989d9e7586dfffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
