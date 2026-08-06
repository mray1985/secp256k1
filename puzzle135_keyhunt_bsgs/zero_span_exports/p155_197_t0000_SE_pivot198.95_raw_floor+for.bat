@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x10012095afcfa3abb  tz=2^90
echo stage=SE_pivot198.95_raw_floor+form56_mul_2^H2
echo tile 0/288230376151711743  range 40048256bf3e8eaec0000000000000000000000:40048256bf3e8eaec00000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 40048256bf3e8eaec0000000000000000000000:40048256bf3e8eaec00000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
