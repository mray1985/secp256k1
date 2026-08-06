@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo PRIORITY 5/10  P155  [SE_pivot198.95_raw]
echo anchor_top=0x10014e6b8feddc2a7  full_zero_span=2^90
echo k512 profile: FIRST 2^32 of zero corridor (anchor tile)
echo range 400539ae3fb770a9c0000000000000000000000:400539ae3fb770a9c00000000000000ffffffff  keys=2^32
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400539ae3fb770a9c0000000000000000000000:400539ae3fb770a9c00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
