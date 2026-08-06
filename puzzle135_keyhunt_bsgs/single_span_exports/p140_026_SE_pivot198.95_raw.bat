@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x1726a93bc98a55  tz=2^87
echo stage=SE_pivot198.95_raw
echo span=2^87  m=2^44  suggested -k 137438953472
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r b93549de4c52a8000000000000000000000:b93549de4c52affffffffffffffffffffff -k 137438953472 -t %THREADS% -s %STATS% -q
pause
