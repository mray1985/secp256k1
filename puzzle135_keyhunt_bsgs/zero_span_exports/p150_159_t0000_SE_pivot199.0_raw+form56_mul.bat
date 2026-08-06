@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x412166374c8b68f  tz=2^91
echo stage=SE_pivot199.0_raw+form56_mul_2^H2
echo tile 0/576460752303423487  range 2090b31ba645b4780000000000000000000000:2090b31ba645b47800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2090b31ba645b4780000000000000000000000:2090b31ba645b47800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
