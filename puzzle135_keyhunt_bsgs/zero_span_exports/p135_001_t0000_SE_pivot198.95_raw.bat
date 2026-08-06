@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x11629f25172617  tz=2^82
echo stage=SE_pivot198.95_raw
echo tile 0/1125899906842623  range 458a7c945c985c00000000000000000000:458a7c945c985c000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 458a7c945c985c00000000000000000000:458a7c945c985c000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
