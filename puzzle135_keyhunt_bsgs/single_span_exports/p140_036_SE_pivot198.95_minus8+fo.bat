@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P140 SINGLE-SPAN BSGS  top=0x11489781ae3ffd9  tz=2^83
echo stage=SE_pivot198.95_minus8+form56_div_2^H2
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P140_compressed.pub" -r 8a44bc0d71ffec800000000000000000000:8a44bc0d71ffecfffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
