@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x80005957273d4bc1d  tz=2^92
echo stage=SE_pivot199.0_raw+form56_mul_2^H2
echo tile 0/1152921504606846975  range 80005957273d4bc1d00000000000000000000000:80005957273d4bc1d000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 80005957273d4bc1d00000000000000000000000:80005957273d4bc1d000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
