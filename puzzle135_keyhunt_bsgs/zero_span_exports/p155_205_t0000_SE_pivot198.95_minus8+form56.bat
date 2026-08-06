@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x80000bc7e461891a65  tz=2^83
echo stage=SE_pivot198.95_minus8+form56_mul_2^H2
echo tile 0/2251799813685247  range 400005e3f230c48d32800000000000000000000:400005e3f230c48d328000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400005e3f230c48d32800000000000000000000:400005e3f230c48d328000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
