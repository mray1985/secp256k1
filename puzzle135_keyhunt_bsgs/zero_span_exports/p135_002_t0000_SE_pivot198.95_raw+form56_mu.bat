@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x13991d60df47d1  tz=2^82
echo stage=SE_pivot198.95_raw+form56_mul_2^H2
echo tile 0/1125899906842623  range 4e6475837d1f4400000000000000000000:4e6475837d1f44000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 4e6475837d1f4400000000000000000000:4e6475837d1f44000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
