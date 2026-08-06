@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 zero-span BSGS  top=0x200012095afcfa3abb  tz=2^90
echo stage=SE_pivot198.95_raw_floor+form56_mul_2^H2
echo tile 0/288230376151711743  range 800048256bf3e8eaec0000000000000000000000:800048256bf3e8eaec00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800048256bf3e8eaec0000000000000000000000:800048256bf3e8eaec00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
