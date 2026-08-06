@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x200013d02e40e87b23  tz=2^90
echo stage=SE_pivot199.0_raw
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80004f40b903a1ec8c0000000000000000000000:80004f40b903a1ec8fffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
