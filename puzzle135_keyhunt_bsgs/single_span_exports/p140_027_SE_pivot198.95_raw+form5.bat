@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x34320f93ee8f9  tz=2^90
echo stage=SE_pivot198.95_raw+form56_mul_2^H2
echo span=2^90  m=2^45  suggested -k 274877906944
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r d0c83e4fba3e40000000000000000000000:d0c83e4fba3e7ffffffffffffffffffffff -k 274877906944 -t %THREADS% -s %STATS% -q
pause
