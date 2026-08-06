@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo PRIORITY 2/10  P140  [SE_pivot198.95_raw]
echo anchor_top=0x1726a93bc98a55  full_zero_span=2^87
echo k512 profile: FIRST 2^32 of zero corridor (anchor tile)
echo range b93549de4c52a8000000000000000000000:b93549de4c52a80000000000000ffffffff  keys=2^32
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r b93549de4c52a8000000000000000000000:b93549de4c52a80000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
