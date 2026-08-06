@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x2000fe4f672767acb  tz=2^79
echo stage=SE_pivot198.0_minus8+form56_mul_sqrt_pN_frac
echo tile 0/140737488355327  range 10007f27b393b3d6580000000000000000000:10007f27b393b3d65800000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 10007f27b393b3d6580000000000000000000:10007f27b393b3d65800000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
