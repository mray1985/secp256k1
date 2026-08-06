@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x100038ef12698bedd  tz=2^85
echo stage=SE_pivot199.0_minus8+form56_div_2^H2
echo tile 0/9007199254740991  range 200071de24d317dba000000000000000000000:200071de24d317dba0000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 200071de24d317dba000000000000000000000:200071de24d317dba0000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
