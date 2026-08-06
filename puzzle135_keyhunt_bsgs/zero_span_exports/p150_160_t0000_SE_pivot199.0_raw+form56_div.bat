@echo off
setlocal
call "%~dp0..\paths.bat"
cd /d "%WORKDIR%"
echo P150 zero-span BSGS  top=0x1038ef12698bedd  tz=2^93
echo stage=SE_pivot199.0_raw+form56_div_2^H2
echo tile 0/2305843009213693951  range 2071de24d317dba00000000000000000000000:2071de24d317dba000000000000000ffffffff
"%KEYHUNT%" -m bsgs -f "%PUBDIR%P150_compressed.pub" -r 2071de24d317dba00000000000000000000000:2071de24d317dba000000000000000ffffffff -k %K_FACTOR% -t %THREADS% -s %STATS% -q
