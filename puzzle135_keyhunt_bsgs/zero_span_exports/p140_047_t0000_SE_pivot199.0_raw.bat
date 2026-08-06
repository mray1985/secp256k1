@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 zero-span BSGS  top=0xc6804def9f3b1  tz=2^88
echo stage=SE_pivot199.0_raw
echo tile 0/72057594037927935  range c6804def9f3b10000000000000000000000:c6804def9f3b100000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r c6804def9f3b10000000000000000000000:c6804def9f3b100000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
