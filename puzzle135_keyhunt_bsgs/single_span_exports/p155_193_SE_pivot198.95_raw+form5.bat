@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P155 SINGLE-SPAN BSGS  top=0x800bc7e461891a65  tz=2^91
echo stage=SE_pivot198.95_raw+form56_mul_2^H2
echo span=2^91  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P155_compressed.pub" -r 4005e3f230c48d3280000000000000000000000:4005e3f230c48d32fffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
