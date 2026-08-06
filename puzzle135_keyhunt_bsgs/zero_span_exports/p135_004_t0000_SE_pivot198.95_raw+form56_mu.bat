@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0xe4aa253984ce1  tz=2^83
echo stage=SE_pivot198.95_raw+form56_mul_sqrt_pN_frac
echo tile 0/2251799813685247  range 7255129cc2670800000000000000000000:7255129cc26708000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 7255129cc2670800000000000000000000:7255129cc26708000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
