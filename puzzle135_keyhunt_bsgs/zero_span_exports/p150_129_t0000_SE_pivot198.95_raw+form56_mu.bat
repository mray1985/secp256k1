@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x410e04e23de7239  tz=2^91
echo stage=SE_pivot198.95_raw+form56_mul_2^H2
echo tile 0/576460752303423487  range 208702711ef391c80000000000000000000000:208702711ef391c800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 208702711ef391c80000000000000000000000:208702711ef391c800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
