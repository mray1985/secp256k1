@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x10004f7cf4034afc3  tz=2^90
echo stage=SE_pivot198.0_raw+form56_div_2^H2
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40013df3d00d2bf0c0000000000000000000000:40013df3d00d2bf0fffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
