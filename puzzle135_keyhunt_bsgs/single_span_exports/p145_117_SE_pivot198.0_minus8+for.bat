@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x10015cbcd3ccf79df  tz=2^80
echo stage=SE_pivot198.0_minus8+form56_mul_2^H2
echo span=2^80  m=2^40  suggested -k 8589934592
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 10015cbcd3ccf79df00000000000000000000:10015cbcd3ccf79dfffffffffffffffffffff -k 8589934592 -t %THREADS% -s %STATS% -q
pause
