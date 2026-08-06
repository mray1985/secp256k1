@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P145 SINGLE-SPAN BSGS  top=0x28006b93b442f9  tz=2^91
echo stage=SE_pivot198.95_raw+form56_div_2^H2
echo span=2^91  m=2^46  suggested -k 549755813888
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P145_compressed.pub" -r 140035c9da217c80000000000000000000000:140035c9da217cfffffffffffffffffffffff -k 549755813888 -t %THREADS% -s %STATS% -q
pause
