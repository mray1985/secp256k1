@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x200a2b11cd66da87  tz=2^83
echo stage=SE_pivot198.95_minus8+form56_mul_2^H2
echo span=2^83  m=2^42  suggested -k 34359738368
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 10051588e6b36d43800000000000000000000:10051588e6b36d43fffffffffffffffffffff -k 34359738368 -t %THREADS% -s %STATS% -q
pause
