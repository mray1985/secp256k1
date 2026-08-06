@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x8001a8f82f04b4805  tz=2^82
echo stage=SE_pivot198.95_minus8+form56_div_2^H2
echo tile 0/1125899906842623  range 20006a3e0bc12d201400000000000000000000:20006a3e0bc12d2014000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 20006a3e0bc12d201400000000000000000000:20006a3e0bc12d2014000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
