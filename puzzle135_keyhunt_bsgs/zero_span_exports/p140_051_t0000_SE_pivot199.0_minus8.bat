@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0x8c6804def9f3b1  tz=2^84
echo stage=SE_pivot199.0_minus8
echo tile 0/4503599627370495  range 8c6804def9f3b1000000000000000000000:8c6804def9f3b10000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8c6804def9f3b1000000000000000000000:8c6804def9f3b10000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
