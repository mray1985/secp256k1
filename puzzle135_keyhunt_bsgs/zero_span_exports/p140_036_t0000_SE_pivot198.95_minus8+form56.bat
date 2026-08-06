@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x11489781ae3ffd9  tz=2^83
echo stage=SE_pivot198.95_minus8+form56_div_2^H2
echo tile 0/2251799813685247  range 8a44bc0d71ffec800000000000000000000:8a44bc0d71ffec8000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8a44bc0d71ffec800000000000000000000:8a44bc0d71ffec8000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
