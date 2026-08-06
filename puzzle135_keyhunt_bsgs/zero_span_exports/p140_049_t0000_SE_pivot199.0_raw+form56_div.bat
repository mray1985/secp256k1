@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x1602d0e088f5fb  tz=2^87
echo stage=SE_pivot199.0_raw+form56_div_2^H2
echo tile 0/36028797018963967  range b016870447afd8000000000000000000000:b016870447afd80000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r b016870447afd8000000000000000000000:b016870447afd80000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
