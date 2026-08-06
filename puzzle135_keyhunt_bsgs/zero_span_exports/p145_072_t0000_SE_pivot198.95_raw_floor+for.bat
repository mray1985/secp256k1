@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x52095afcfa3abb  tz=2^90
echo stage=SE_pivot198.95_raw_floor+form56_mul_2^H2
echo tile 0/288230376151711743  range 148256bf3e8eaec0000000000000000000000:148256bf3e8eaec00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 148256bf3e8eaec0000000000000000000000:148256bf3e8eaec00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
