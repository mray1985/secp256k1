@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x80000824cb1ad37ccf  tz=2^88
echo stage=SE_pivot198.0_raw+form56_mul_sqrt_pN_frac
echo tile 0/72057594037927935  range 80000824cb1ad37ccf0000000000000000000000:80000824cb1ad37ccf00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80000824cb1ad37ccf0000000000000000000000:80000824cb1ad37ccf00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
