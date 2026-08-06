@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x4004f7cf4034afc3  tz=2^92
echo stage=SE_pivot199.0_raw+form56_div_2^H2
echo span=2^92  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4004f7cf4034afc300000000000000000000000:4004f7cf4034afc3fffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
