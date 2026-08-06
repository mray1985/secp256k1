@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 SINGLE-SPAN BSGS  top=0x11629f25172617  tz=2^82
echo stage=SE_pivot198.95_raw
echo span=2^82  m=2^41  suggested -k 17179869184
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 458a7c945c985c00000000000000000000:458a7c945c985fffffffffffffffffffff -k 17179869184 -t %THREADS% -s %STATS% -q
pause
