@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x800bc7e461891a65  tz=2^91
echo stage=SE_pivot198.95_raw+form56_mul_2^H2
echo tile 0/576460752303423487  range 4005e3f230c48d3280000000000000000000000:4005e3f230c48d32800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4005e3f230c48d3280000000000000000000000:4005e3f230c48d32800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
