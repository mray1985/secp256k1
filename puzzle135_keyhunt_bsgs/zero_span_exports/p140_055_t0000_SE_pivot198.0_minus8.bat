@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x20c6804def9f3b1  tz=2^82
echo stage=SE_pivot198.0_minus8
echo tile 0/1125899906842623  range 831a0137be7cec400000000000000000000:831a0137be7cec4000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 831a0137be7cec400000000000000000000:831a0137be7cec4000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
