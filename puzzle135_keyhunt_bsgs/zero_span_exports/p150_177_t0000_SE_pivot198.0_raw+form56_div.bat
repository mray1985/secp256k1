@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x4038ef12698bedd  tz=2^91
echo stage=SE_pivot198.0_raw+form56_div_2^H2
echo tile 0/576460752303423487  range 201c778934c5f6e80000000000000000000000:201c778934c5f6e800000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 201c778934c5f6e80000000000000000000000:201c778934c5f6e800000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
