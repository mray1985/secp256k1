@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x800012095afcfa3abb  tz=2^88
echo stage=SE_pivot198.0_raw_floor+form56_mul_2^H2
echo tile 0/72057594037927935  range 800012095afcfa3abb0000000000000000000000:800012095afcfa3abb00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800012095afcfa3abb0000000000000000000000:800012095afcfa3abb00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
