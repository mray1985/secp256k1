@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x8c6804def9f3b1  tz=2^84
echo stage=SE_pivot199.0_minus8
echo span=2^84  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8c6804def9f3b1000000000000000000000:8c6804def9f3b1fffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
