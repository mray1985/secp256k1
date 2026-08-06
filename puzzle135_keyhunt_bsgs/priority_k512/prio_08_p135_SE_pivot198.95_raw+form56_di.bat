@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo PRIORITY 8/10  P135  [SE_pivot198.95_raw+form56_div_2^H2]
echo anchor_top=0x1ed82f5c47b8a5  full_zero_span=2^82
echo k512 profile: FIRST 2^32 of zero corridor (anchor tile)
echo range 7b60bd711ee29400000000000000000000:7b60bd711ee294000000000000ffffffff  keys=2^32
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 7b60bd711ee29400000000000000000000:7b60bd711ee294000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
