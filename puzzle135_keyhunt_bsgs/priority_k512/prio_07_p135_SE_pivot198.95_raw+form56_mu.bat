@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo PRIORITY 7/10  P135  [SE_pivot198.95_raw+form56_mul_2^H2]
echo anchor_top=0x13991d60df47d1  full_zero_span=2^82
echo k512 profile: FIRST 2^32 of zero corridor (anchor tile)
echo range 4e6475837d1f4400000000000000000000:4e6475837d1f44000000000000ffffffff  keys=2^32
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 4e6475837d1f4400000000000000000000:4e6475837d1f44000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
