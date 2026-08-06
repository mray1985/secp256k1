@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0xc6804def9f3b1  tz=2^88
echo stage=SE_pivot199.0_raw
echo span=2^88  m=2^44  suggested -k 137438953472
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r c6804def9f3b10000000000000000000000:c6804def9f3b1ffffffffffffffffffffff -k 137438953472 -t %THREADS% -s %STATS% -q
pause
