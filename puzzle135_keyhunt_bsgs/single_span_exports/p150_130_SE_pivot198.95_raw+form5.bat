@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x81a8f82f04b4805  tz=2^90
echo stage=SE_pivot198.95_raw+form56_div_2^H2
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 206a3e0bc12d20140000000000000000000000:206a3e0bc12d2017ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
