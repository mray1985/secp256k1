@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo PRIORITY 3/10  P145  [SE_pivot198.95_raw]
echo anchor_top=0x14829361c760ed  full_zero_span=2^92
echo k512 profile: FIRST 2^32 of zero corridor (anchor tile)
echo range 14829361c760ed00000000000000000000000:14829361c760ed000000000000000ffffffff  keys=2^32
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 14829361c760ed00000000000000000000000:14829361c760ed000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
