@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x4012095afcfa3abb  tz=2^82
echo stage=SE_pivot198.95_minus8_floor+form56_mul_2^H2
echo tile 0/1125899906842623  range 10048256bf3e8eaec00000000000000000000:10048256bf3e8eaec000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 10048256bf3e8eaec00000000000000000000:10048256bf3e8eaec000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
