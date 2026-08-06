@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x1449b8a1b2bcd3  tz=2^92
echo stage=SE_pivot199.0_raw+form56_div_2^H2
echo span=2^92  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 1449b8a1b2bcd300000000000000000000000:1449b8a1b2bcd3fffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
