@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x8000005957273d4bc1d  tz=2^84
echo stage=SE_pivot199.0_minus8+form56_mul_2^H2
echo span=2^84  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000005957273d4bc1d000000000000000000000:8000005957273d4bc1dfffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
