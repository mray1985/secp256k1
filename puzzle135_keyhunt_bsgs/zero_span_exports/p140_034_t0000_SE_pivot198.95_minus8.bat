@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x11726a93bc98a55  tz=2^83
echo stage=SE_pivot198.95_minus8
echo tile 0/2251799813685247  range 8b93549de4c52a800000000000000000000:8b93549de4c52a8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8b93549de4c52a800000000000000000000:8b93549de4c52a8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
