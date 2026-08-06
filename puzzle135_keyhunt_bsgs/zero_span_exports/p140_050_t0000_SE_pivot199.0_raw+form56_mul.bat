@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x1465b19477bdd5  tz=2^87
echo stage=SE_pivot199.0_raw+form56_mul_sqrt_pN_frac
echo tile 0/36028797018963967  range a32d8ca3bdeea8000000000000000000000:a32d8ca3bdeea80000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r a32d8ca3bdeea8000000000000000000000:a32d8ca3bdeea80000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
