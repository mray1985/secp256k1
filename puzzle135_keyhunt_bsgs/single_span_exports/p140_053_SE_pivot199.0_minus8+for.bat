@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x11602d0e088f5fb  tz=2^83
echo stage=SE_pivot199.0_minus8+form56_div_2^H2
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8b016870447afd800000000000000000000:8b016870447afdfffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
