@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 SINGLE-SPAN BSGS  top=0x100038ef12698bedd  tz=2^85
echo stage=SE_pivot199.0_minus8+form56_div_2^H2
echo span=2^85  m=2^43  suggested -k 68719476736
echo ONE meet-in-the-middle — not sequential 2^32 tiles
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200071de24d317dba000000000000000000000:200071de24d317dbbfffffffffffffffffffff -k 68719476736 -t %THREADS% -s %STATS% -q
pause
