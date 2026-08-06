@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x11602d0e088f5fb  tz=2^83
echo stage=SE_pivot199.0_minus8+form56_div_2^H2
echo tile 0/2251799813685247  range 8b016870447afd800000000000000000000:8b016870447afd8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8b016870447afd800000000000000000000:8b016870447afd8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
