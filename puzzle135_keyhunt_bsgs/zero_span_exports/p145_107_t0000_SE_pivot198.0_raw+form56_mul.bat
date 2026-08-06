@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x20fe4f672767acb  tz=2^87
echo stage=SE_pivot198.0_raw+form56_mul_sqrt_pN_frac
echo tile 0/36028797018963967  range 107f27b393b3d658000000000000000000000:107f27b393b3d6580000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 107f27b393b3d658000000000000000000000:107f27b393b3d6580000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
