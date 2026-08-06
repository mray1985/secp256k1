@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x9ea2742f79c4e5  tz=2^79
echo stage=SE_pivot198.0_minus8+form56_mul_sqrt_pN_frac
echo tile 0/140737488355327  range 4f513a17bce27280000000000000000000:4f513a17bce272800000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 4f513a17bce27280000000000000000000:4f513a17bce272800000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
