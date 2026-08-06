@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x2a2b11cd66da87  tz=2^91
echo stage=SE_pivot198.95_raw+form56_mul_2^H2
echo tile 0/576460752303423487  range 151588e6b36d4380000000000000000000000:151588e6b36d43800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 151588e6b36d4380000000000000000000000:151588e6b36d43800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
