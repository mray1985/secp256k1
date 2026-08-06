@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo PRIORITY 4/10  P150  [SE_pivot198.95_raw]
echo anchor_top=0x40ef87d89980a95  full_zero_span=2^91
echo k512 profile: FIRST 2^32 of zero corridor (anchor tile)
echo range 2077c3ec4cc054a80000000000000000000000:2077c3ec4cc054a800000000000000ffffffff  keys=2^32
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2077c3ec4cc054a80000000000000000000000:2077c3ec4cc054a800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
