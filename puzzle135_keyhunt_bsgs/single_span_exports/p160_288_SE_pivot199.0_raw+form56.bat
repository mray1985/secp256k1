@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P160 SINGLE-SPAN BSGS  top=0x8000464de13f59e9d  tz=2^92
echo stage=SE_pivot199.0_raw+form56_div_2^H2
echo span=2^92  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P160_compressed.pub" -r 8000464de13f59e9d00000000000000000000000:8000464de13f59e9dfffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
