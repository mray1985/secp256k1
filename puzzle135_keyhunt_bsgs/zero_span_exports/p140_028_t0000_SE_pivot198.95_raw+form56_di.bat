@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x1489781ae3ffd9  tz=2^87
echo stage=SE_pivot198.95_raw+form56_div_2^H2
echo tile 0/36028797018963967  range a44bc0d71ffec8000000000000000000000:a44bc0d71ffec80000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r a44bc0d71ffec8000000000000000000000:a44bc0d71ffec80000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
