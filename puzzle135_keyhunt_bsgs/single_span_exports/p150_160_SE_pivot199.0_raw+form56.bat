@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x1038ef12698bedd  tz=2^93
echo stage=SE_pivot199.0_raw+form56_div_2^H2
echo span=2^93  m=2^47  suggested -k 1099511627776
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2071de24d317dba00000000000000000000000:2071de24d317dbbfffffffffffffffffffffff -k 1099511627776 -t %THREADS% -s %STATS% -q
pause
