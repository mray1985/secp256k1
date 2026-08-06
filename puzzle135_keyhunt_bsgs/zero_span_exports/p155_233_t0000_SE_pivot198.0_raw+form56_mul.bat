@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x800126a4322cd9ebb  tz=2^87
echo stage=SE_pivot198.0_raw+form56_mul_sqrt_pN_frac
echo tile 0/36028797018963967  range 4000935219166cf5d8000000000000000000000:4000935219166cf5d80000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4000935219166cf5d8000000000000000000000:4000935219166cf5d80000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
