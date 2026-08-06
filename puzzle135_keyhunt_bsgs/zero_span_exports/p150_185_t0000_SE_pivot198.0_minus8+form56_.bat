@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x400038ef12698bedd  tz=2^83
echo stage=SE_pivot198.0_minus8+form56_div_2^H2
echo tile 0/2251799813685247  range 20001c778934c5f6e800000000000000000000:20001c778934c5f6e8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20001c778934c5f6e800000000000000000000:20001c778934c5f6e8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
