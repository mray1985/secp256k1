@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo PRIORITY 6/10  P160  [SE_pivot198.95_raw]
echo anchor_top=0x2000127c830ca26243  full_zero_span=2^90
echo k512 profile: FIRST 2^32 of zero corridor (anchor tile)
echo range 800049f20c3289890c0000000000000000000000:800049f20c3289890c00000000000000ffffffff  keys=2^32
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800049f20c3289890c0000000000000000000000:800049f20c3289890c00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
