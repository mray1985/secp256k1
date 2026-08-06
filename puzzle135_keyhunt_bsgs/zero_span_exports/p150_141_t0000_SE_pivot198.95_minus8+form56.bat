@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x40010e04e23de7239  tz=2^83
echo stage=SE_pivot198.95_minus8+form56_mul_2^H2
echo tile 0/2251799813685247  range 20008702711ef391c800000000000000000000:20008702711ef391c8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20008702711ef391c800000000000000000000:20008702711ef391c8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
