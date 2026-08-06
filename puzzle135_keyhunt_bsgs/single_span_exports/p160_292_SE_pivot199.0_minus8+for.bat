@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x800000464de13f59e9d  tz=2^84
echo stage=SE_pivot199.0_minus8+form56_div_2^H2
echo span=2^84  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 800000464de13f59e9d000000000000000000000:800000464de13f59e9dfffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
