@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x11726a93bc98a55  tz=2^83
echo stage=SE_pivot198.95_minus8
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8b93549de4c52a800000000000000000000:8b93549de4c52afffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
