@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo PRIORITY 10/10  P135  [SE_pivot198.95_raw+form56_mul_sqrt_pN_frac]
echo anchor_top=0xe4aa253984ce1  full_zero_span=2^83
echo k512 profile: FIRST 2^32 of zero corridor (anchor tile)
echo range 7255129cc2670800000000000000000000:7255129cc26708000000000000ffffffff  keys=2^32
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 7255129cc2670800000000000000000000:7255129cc26708000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
pause
