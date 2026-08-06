@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x401a613e2bfa5a8d  tz=2^87
echo stage=SE_pivot198.0_raw+form56_mul_sqrt_pN_frac
echo tile 0/36028797018963967  range 200d309f15fd2d468000000000000000000000:200d309f15fd2d4680000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200d309f15fd2d468000000000000000000000:200d309f15fd2d4680000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
