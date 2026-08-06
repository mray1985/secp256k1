@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x400004f7cf4034afc3  tz=2^84
echo stage=SE_pivot199.0_minus8+form56_div_2^H2
echo span=2^84  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 400004f7cf4034afc3000000000000000000000:400004f7cf4034afc3fffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
