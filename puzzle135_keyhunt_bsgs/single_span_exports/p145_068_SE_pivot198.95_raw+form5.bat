@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x2a2b11cd66da87  tz=2^91
echo stage=SE_pivot198.95_raw+form56_mul_2^H2
echo span=2^91  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 151588e6b36d4380000000000000000000000:151588e6b36d43fffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
