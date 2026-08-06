@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x40001a613e2bfa5a8d  tz=2^79
echo stage=SE_pivot198.0_minus8+form56_mul_sqrt_pN_frac
echo tile 0/140737488355327  range 20000d309f15fd2d4680000000000000000000:20000d309f15fd2d46800000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20000d309f15fd2d4680000000000000000000:20000d309f15fd2d46800000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
