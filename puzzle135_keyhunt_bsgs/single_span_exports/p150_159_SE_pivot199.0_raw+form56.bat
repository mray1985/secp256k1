@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x412166374c8b68f  tz=2^91
echo stage=SE_pivot199.0_raw+form56_mul_2^H2
echo span=2^91  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2090b31ba645b4780000000000000000000000:2090b31ba645b47fffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
