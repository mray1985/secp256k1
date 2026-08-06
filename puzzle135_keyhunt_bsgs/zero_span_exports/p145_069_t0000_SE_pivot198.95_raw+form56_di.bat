@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 zero-span BSGS  top=0x28006b93b442f9  tz=2^91
echo stage=SE_pivot198.95_raw+form56_div_2^H2
echo tile 0/576460752303423487  range 140035c9da217c80000000000000000000000:140035c9da217c800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 140035c9da217c80000000000000000000000:140035c9da217c800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
