@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x80000126a4322cd9ebb  tz=2^79
echo stage=SE_pivot198.0_minus8+form56_mul_sqrt_pN_frac
echo tile 0/140737488355327  range 400000935219166cf5d80000000000000000000:400000935219166cf5d800000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400000935219166cf5d80000000000000000000:400000935219166cf5d800000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
