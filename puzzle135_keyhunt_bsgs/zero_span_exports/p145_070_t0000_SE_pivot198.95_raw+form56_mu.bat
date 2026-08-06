@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x11da8f3ee0d2e39  tz=2^88
echo stage=SE_pivot198.95_raw+form56_mul_sqrt_pN_frac
echo tile 0/72057594037927935  range 11da8f3ee0d2e390000000000000000000000:11da8f3ee0d2e3900000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 11da8f3ee0d2e390000000000000000000000:11da8f3ee0d2e3900000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
