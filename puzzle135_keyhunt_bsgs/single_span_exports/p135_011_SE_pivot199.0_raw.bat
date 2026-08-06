@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P135 SINGLE-SPAN BSGS  top=0x25441dcaa45cf  tz=2^85
echo stage=SE_pivot199.0_raw
echo span=2^85  m=2^43  suggested -k 68719476736
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P135_compressed.pub" -r 4a883b9548b9e000000000000000000000:4a883b9548b9ffffffffffffffffffffff -k 68719476736 -t %THREADS% -s %STATS% -q
pause
