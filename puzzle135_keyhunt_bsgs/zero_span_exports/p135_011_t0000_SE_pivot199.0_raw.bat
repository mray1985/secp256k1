@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 zero-span BSGS  top=0x25441dcaa45cf  tz=2^85
echo stage=SE_pivot199.0_raw
echo tile 0/9007199254740991  range 4a883b9548b9e000000000000000000000:4a883b9548b9e0000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 4a883b9548b9e000000000000000000000:4a883b9548b9e0000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
