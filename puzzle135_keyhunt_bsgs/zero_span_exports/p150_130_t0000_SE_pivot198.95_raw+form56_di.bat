@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x81a8f82f04b4805  tz=2^90
echo stage=SE_pivot198.95_raw+form56_div_2^H2
echo tile 0/288230376151711743  range 206a3e0bc12d20140000000000000000000000:206a3e0bc12d201400000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 206a3e0bc12d20140000000000000000000000:206a3e0bc12d201400000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
