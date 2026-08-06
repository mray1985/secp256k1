@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo PRIORITY 9/10  P145  [SE_pivot198.95_raw+form56_mul_sqrt_pN_frac]
echo anchor_top=0x11da8f3ee0d2e39  full_zero_span=2^88
echo k512 profile: FIRST 2^32 of zero corridor (anchor tile)
echo range 11da8f3ee0d2e390000000000000000000000:11da8f3ee0d2e3900000000000000ffffffff  keys=2^32
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 11da8f3ee0d2e390000000000000000000000:11da8f3ee0d2e3900000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
