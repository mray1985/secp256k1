@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x100128a8fa8708e61  tz=2^90
echo stage=SE_pivot198.95_raw+form56_div_2^H2
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4004a2a3ea1c239840000000000000000000000:4004a2a3ea1c23987ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
