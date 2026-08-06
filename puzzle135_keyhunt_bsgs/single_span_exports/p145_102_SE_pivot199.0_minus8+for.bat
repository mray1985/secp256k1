@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x100449b8a1b2bcd3  tz=2^84
echo stage=SE_pivot199.0_minus8+form56_div_2^H2
echo span=2^84  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 100449b8a1b2bcd3000000000000000000000:100449b8a1b2bcd3fffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
