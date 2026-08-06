@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x65441dcaa45cf  tz=2^84
echo stage=SE_pivot198.0_minus8
echo tile 0/4503599627370495  range 65441dcaa45cf000000000000000000000:65441dcaa45cf0000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 65441dcaa45cf000000000000000000000:65441dcaa45cf0000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
