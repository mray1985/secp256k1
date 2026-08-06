@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x1726a93bc98a55  tz=2^87
echo stage=SE_pivot198.95_raw
echo tile 0/36028797018963967  range b93549de4c52a8000000000000000000000:b93549de4c52a80000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r b93549de4c52a8000000000000000000000:b93549de4c52a80000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
