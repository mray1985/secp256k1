@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 zero-span BSGS  top=0x800ca05a66ea9b87  tz=2^91
echo stage=SE_pivot199.0_raw+form56_mul_2^H2
echo tile 0/576460752303423487  range 4006502d33754dc380000000000000000000000:4006502d33754dc3800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4006502d33754dc380000000000000000000000:4006502d33754dc3800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
