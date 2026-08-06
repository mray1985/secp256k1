@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x8000005957273d4bc1d  tz=2^84
echo stage=SE_pivot199.0_minus8+form56_mul_2^H2
echo tile 0/4503599627370495  range 8000005957273d4bc1d000000000000000000000:8000005957273d4bc1d0000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000005957273d4bc1d000000000000000000000:8000005957273d4bc1d0000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
