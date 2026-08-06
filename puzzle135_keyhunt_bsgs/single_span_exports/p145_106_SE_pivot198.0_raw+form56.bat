@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x4449b8a1b2bcd3  tz=2^90
echo stage=SE_pivot198.0_raw+form56_div_2^H2
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 11126e286caf34c0000000000000000000000:11126e286caf34fffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
