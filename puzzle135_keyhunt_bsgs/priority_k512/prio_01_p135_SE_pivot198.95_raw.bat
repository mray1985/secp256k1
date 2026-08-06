@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo PRIORITY 1/10  P135  [SE_pivot198.95_raw]
echo anchor_top=0x11629f25172617  full_zero_span=2^82
echo k512 profile: FIRST 2^32 of zero corridor (anchor tile)
echo range 458a7c945c985c00000000000000000000:458a7c945c985c000000000000ffffffff  keys=2^32
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 458a7c945c985c00000000000000000000:458a7c945c985c000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
