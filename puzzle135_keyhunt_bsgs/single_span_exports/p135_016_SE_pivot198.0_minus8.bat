@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 SINGLE-SPAN BSGS  top=0x65441dcaa45cf  tz=2^84
echo stage=SE_pivot198.0_minus8
echo span=2^84  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 65441dcaa45cf000000000000000000000:65441dcaa45cffffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
