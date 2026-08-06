@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x80001e64b958aa0f6d  tz=2^88
echo stage=SE_pivot198.95_raw+form56_mul_sqrt_pN_frac
echo tile 0/72057594037927935  range 80001e64b958aa0f6d0000000000000000000000:80001e64b958aa0f6d00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80001e64b958aa0f6d0000000000000000000000:80001e64b958aa0f6d00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
